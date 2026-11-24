"""Feedback eligibility, retention, and aggregate metrics."""
from collections import Counter
from itertools import permutations
import json

from prometheus_client.core import GaugeMetricFamily
from sqlalchemy import func, or_, select

from .contracts import CATEGORIES, FeedbackState
from .storage import FeedbackRow, JobRow

FEEDBACK_RETENTION = 30 * 86400
FEEDBACK_QUOTA = 20
FEEDBACK_WINDOW = 86400
FEEDBACK_MAX_REQUEST = 8192
AI_STAGES = {'classification': 'classifier', 'description': 'description'}


def feedback_analysis(db, draft):
    current = draft.get('analysis')
    if not current:
        return None, {}
    if current['status'] not in ('succeeded', 'failed'):
        return current['job_id'], {}
    row = db.get(JobRow, current['job_id'])
    if row is None or row.draft_id != draft['id']:
        return None, {}
    job = json.loads(row.content)
    executions = {}
    for kind, stage in AI_STAGES.items():
        execution = job.get(stage) or {}
        if execution.get('status') != 'ok':
            continue
        if kind == 'description' and not execution['result']['suggested_description'].strip():
            continue
        executions[kind] = execution
    return row.id, executions


def feedback_state(db, draft_id, job_id, executions):
    target = FeedbackRow.draft_id == draft_id
    if job_id is not None:
        target = or_(target, FeedbackRow.job_id == job_id)
    submitted = set(db.scalars(select(FeedbackRow.kind).where(target)))

    def status(kind):
        if kind in submitted:
            return 'submitted'
        return 'open' if kind == 'experience' or kind in executions else 'unavailable'

    return FeedbackState(
        job_id=job_id,
        classification=status('classification'),
        description=status('description'),
        experience=status('experience'),
    )


class FeedbackCollector:
    def __init__(self, store, clock):
        self.store = store
        self.clock = clock

    def collect(self):
        fields = (FeedbackRow.kind, FeedbackRow.verdict, FeedbackRow.predicted_category,
                  FeedbackRow.suggested_category, FeedbackRow.rating)
        query = select(*fields, func.count()).where(
            FeedbackRow.created_at > self.clock() - FEEDBACK_RETENTION,
            FeedbackRow.simulated.is_(False),
        ).group_by(*fields)

        classification, corrections, description, ratings = Counter(), Counter(), Counter(), Counter()
        with self.store.session() as db:
            for kind, verdict, predicted, suggested, rating, count in db.execute(query):
                if kind == 'classification':
                    classification[verdict, predicted] += count
                    if suggested:
                        corrections[predicted, suggested] += count
                elif kind == 'description':
                    description[verdict] += count
                elif kind == 'experience':
                    ratings[rating] += count

        metric = GaugeMetricFamily('civicfix_feedback_classification_votes',
                                   'Real classification votes in the last 30 days.',
                                   labels=['verdict', 'predicted_category'])
        for category in CATEGORIES:
            for verdict in ('correct', 'incorrect'):
                metric.add_metric([verdict, category], classification[verdict, category])
        yield metric

        metric = GaugeMetricFamily('civicfix_feedback_classification_corrections',
                                   'Real suggested category corrections in the last 30 days.',
                                   labels=['predicted_category', 'suggested_category'])
        for predicted, suggested in permutations(CATEGORIES, 2):
            metric.add_metric([predicted, suggested], corrections[predicted, suggested])
        yield metric

        metric = GaugeMetricFamily('civicfix_feedback_description_votes',
                                   'Real description votes in the last 30 days.', labels=['verdict'])
        for verdict in ('helpful', 'inaccurate'):
            metric.add_metric([verdict], description[verdict])
        yield metric

        metric = GaugeMetricFamily('civicfix_feedback_experience_ratings',
                                   'Real app experience ratings in the last 30 days.', labels=['rating'])
        for rating in range(1, 6):
            metric.add_metric([str(rating)], ratings[rating])
        yield metric
