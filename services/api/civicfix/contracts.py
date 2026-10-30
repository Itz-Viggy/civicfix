"""Executable application contracts; no model SDK imports."""
from typing import Annotated, Literal
import math
import re
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CATEGORIES = ['pothole','broken_streetlight','damaged_sign','leaking_hydrant','illegal_dumping']
Category = Literal['pothole','broken_streetlight','damaged_sign','leaking_hydrant','illegal_dumping']
Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, strict=True)
class LocationInput(Strict):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    label: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
    source: Literal['manual','map','browser'] = 'manual'
    accuracy: float | None = Field(default=None, ge=0, le=100000)
class DraftCreate(Strict):
    user_observations: Text = ''
class DraftPatch(Strict):
    location: LocationInput | None = None
    user_observations: Text | None = None
    category: Category | None = None
    description: Text | None = None
class Confirm(Strict):
    confirmed: Literal[True]
class Analyze(Strict):
    acknowledged: Literal[True]
    disclosure_version: Literal['local-v1']
class Resolve(Strict):
    reason: Annotated[str, StringConstraints(strip_whitespace=True,min_length=1,max_length=1000)]
    acknowledged: Literal[True]
class Review(Confirm):
    nonemergency_confirmed: Literal[True]
class Empty(Strict):
    pass
class ClassifierResult(Strict):
    predicted_category: Category
    scores: dict[Category,float]
    top1_margin: float = Field(ge=0)
    mode: Literal['closed_set'] = 'closed_set'
    score_kind: Literal['cosine_similarity'] = 'cosine_similarity'
    # Existing classifier includes this duplicate metadata flag.
    simulated: bool = False
    @model_validator(mode='after')
    def valid_scores(self):
        if set(self.scores) != set(CATEGORIES) or any(not math.isfinite(v) or abs(v)>1.00001 for v in self.scores.values()):
            raise ValueError('Exactly five finite cosine scores required')
        ordered=sorted(CATEGORIES,key=lambda c:-self.scores[c])
        if self.predicted_category != ordered[0] or abs(self.top1_margin-(self.scores[ordered[0]]-self.scores[ordered[1]]))>1e-5:
            raise ValueError('Inconsistent classifier winner or margin')
        return self
ReasonCode = Literal['poor_image_quality','no_supported_issue','multiple_issues','insufficient_visual_evidence','operating_status_not_visible','other_uncertainty']
class Clarification(Strict):
    code: ReasonCode
    detail: Annotated[str,StringConstraints(strip_whitespace=True,max_length=500)] = ''
class DescriptionResult(Strict):
    category_suggestion: Category | None
    outcome: Literal['supported','unclear','unsupported']
    visible_observations: list[Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=500)]] = Field(max_length=10)
    suggested_description: Text
    clarification_reasons: list[Clarification] = Field(max_length=10)
    @model_validator(mode='after')
    def consistency(self):
        if len(self.suggested_description.split())>60 or len(re.findall(r'[.!?](?:\s|$)',self.suggested_description))>2:
            raise ValueError('Description exceeds two sentences or 60 words')
        if self.outcome=='supported' and (not self.category_suggestion or not self.suggested_description or not self.visible_observations or self.clarification_reasons):
            raise ValueError('Supported output needs facts, category, description and no clarification')
        if self.outcome!='supported' and not self.clarification_reasons:
            raise ValueError('Uncertain output needs clarification')
        if self.outcome=='unsupported' and self.category_suggestion is not None:
            raise ValueError('Unsupported category must be null')
        return self
class PhotoView(BaseModel):
    id: str
    mime_type: str
    width: int
    height: int
    bytes: int
    preprocessing_version: str
    preview_url: str
    download_url: str
class LocationView(LocationInput):
    confirmed: bool
    confirmed_at: str | None
    boundary_status: str
class FieldSources(BaseModel):
    category: Literal['clip','qwen','user'] | None
    description: Literal['clip','qwen','user'] | None
class StageError(BaseModel):
    code: str
    message: str
class ClassifierExecution(BaseModel):
    status: Literal['ok','error']
    result: ClassifierResult | None = None
    error: StageError | None = None
    metadata: dict[str,object] | None = None
class DescriptionExecution(BaseModel):
    status: Literal['ok','error']
    result: DescriptionResult | None = None
    error: StageError | None = None
    metadata: dict[str,object] | None = None
class AnalysisView(BaseModel):
    job_id: str
    status: str
    classifier: ClassifierExecution | None
    description: DescriptionExecution | None
    reason_codes: list[str]
class Eligibility(BaseModel):
    can_analyze: bool
    can_review: bool
    can_prepare: bool
    reason_codes: list[str]
class RouteView(BaseModel):
    status: Literal['resolved','unresolved']
    route_id: str | None
    jurisdiction: str | None
    destination_name: str | None
    portal_url: str | None
    rules_version: str
    boundary_version: str
    source_urls: list[str]
    verified_at: str
    reason_codes: list[str]
    guidance: str | None = None
class ManualResolutionView(BaseModel):
    reason: str
    corrected_at: str
    resolved_reason_codes: list[str]
class ProcessingAcknowledgement(BaseModel):
    disclosure_version: str
    acknowledged_at: str
    config_digest: str
class DraftView(BaseModel):
    id: str
    revision: int
    state: str
    created_at: str
    updated_at: str
    expires_at: str
    photo: PhotoView | None
    location: LocationView | None
    user_observations: str
    category: Category | None
    description: str
    field_sources: FieldSources
    analysis: AnalysisView | None
    processing_acknowledgement: ProcessingAcknowledgement | None
    manual_resolution: ManualResolutionView | None
    route: RouteView | None
    review_revision: int | None
    reviewed_at: str | None
    prepared_revision: int | None
    prepared_at: str | None
    eligibility: Eligibility
class DraftResponse(BaseModel):
    draft: DraftView
