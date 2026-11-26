"""Render a printable civic issue report from a reviewed draft."""
from datetime import datetime
from io import BytesIO
from urllib.parse import urlsplit
from xml.sax.saxutils import escape, quoteattr
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Flowable, Frame, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

CATEGORY_LABELS = {
    'pothole': 'Pothole',
    'broken_streetlight': 'Broken streetlight',
    'damaged_sign': 'Damaged sign',
    'leaking_hydrant': 'Leaking hydrant',
    'illegal_dumping': 'Suspected dumping',
}
GREEN = colors.HexColor('#173F35')
INK = colors.HexColor('#263C34')
MUTED = colors.HexColor('#50645B')
LINE = colors.HexColor('#D7E3D8')
TINT = colors.HexColor('#F1F6EE')
MARGIN = 48
PAGE_WIDTH, PAGE_HEIGHT = letter
BODY_WIDTH = PAGE_WIDTH - 2 * MARGIN
REGULAR = 'CivicFix Sans'
BOLD = 'CivicFix Sans Bold'
pdfmetrics.registerFont(TTFont(REGULAR, 'Vera.ttf'))
pdfmetrics.registerFont(TTFont(BOLD, 'VeraBd.ttf'))

BODY = ParagraphStyle('body', fontName=REGULAR, fontSize=11, leading=16, textColor=INK)
TITLE = ParagraphStyle('title', parent=BODY, fontName=BOLD, fontSize=32, leading=37, textColor=GREEN)
LABEL = ParagraphStyle('label', parent=BODY, fontName=BOLD, fontSize=9, leading=12,
                       textColor=GREEN, spaceAfter=4)
DETAIL = ParagraphStyle('detail', parent=BODY, fontSize=9, leading=13, textColor=MUTED)
LOCATION = ParagraphStyle('location', parent=BODY, fontName=BOLD, fontSize=13, leading=18)


def paragraph(value, style=BODY):
    # ReportLab interprets a subset of XML. User-entered text is always literal.
    return Paragraph('<br/>'.join(escape(line) for line in value.splitlines()), style)


class IssuePhoto(Flowable):
    def __init__(self, photo):
        super().__init__()
        self.image = ImageReader(BytesIO(photo))

    def wrap(self, available_width, available_height):
        self.width = available_width
        self.height = 230
        return self.width, self.height

    def draw(self):
        width, height = self.image.getSize()
        scale = min((self.width - 16) / width, (self.height - 16) / height)
        width, height = width * scale, height * scale
        self.canv.setFillColor(TINT)
        self.canv.roundRect(0, 0, self.width, self.height, 8, stroke=0, fill=1)
        self.canv.drawImage(self.image, (self.width - width) / 2, (self.height - height) / 2,
                            width=width, height=height)


def page_details(canvas, document):
    canvas.saveState()
    canvas.setFillColor(GREEN)
    canvas.setFont(BOLD, 17)
    canvas.drawString(MARGIN, 744, 'CivicFix')
    canvas.setFont(BOLD, 9)
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 745, 'PREPARED LOCALLY / NOT SUBMITTED')
    canvas.setStrokeColor(LINE)
    canvas.line(MARGIN, 730, PAGE_WIDTH - MARGIN, 730)
    canvas.line(MARGIN, 43, PAGE_WIDTH - MARGIN, 43)
    canvas.setFillColor(MUTED)
    canvas.setFont(REGULAR, 9)
    canvas.drawString(MARGIN, 27, 'Gainesville, Florida  /  Nonemergency issue report')
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 27, f'Page {document.page}')
    canvas.restoreState()


def render_pdf(report, photo):
    location = report['location']
    route = report['destination']
    title = f"{CATEGORY_LABELS[report['category']]} report"
    prepared = datetime.fromisoformat(report['prepared_at'])
    try:
        prepared = prepared.astimezone(ZoneInfo('America/New_York'))
    except ZoneInfoNotFoundError:
        pass

    location_card = [
        paragraph('CONFIRMED LOCATION', LABEL),
        paragraph(' '.join(location['label'].split()), LOCATION),
        paragraph(f"{location['latitude']:.6f}, {location['longitude']:.6f}", DETAIL),
    ]
    if roads := route.get('road_names'):
        location_card.append(paragraph('Mapped road: ' + ', '.join(roads), DETAIL))
    location_box = Table([[location_card]], colWidths=[BODY_WIDTH], style=TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), TINT),
        ('LINEBEFORE', (0, 0), (0, 0), 2, GREEN),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
    ]))
    story = [
        paragraph(title, TITLE),
        paragraph(f'Prepared {prepared:%B} {prepared.day}, {prepared.year}', DETAIL),
        Spacer(1, 16), location_box, Spacer(1, 16),
        KeepTogether([paragraph('ISSUE PHOTO', LABEL), IssuePhoto(photo)]), Spacer(1, 16),
        CondPageBreak(48), paragraph('ISSUE DESCRIPTION', LABEL), paragraph(report['description']),
    ]
    if notes := report['user_observations']:
        story.extend([Spacer(1, 13), CondPageBreak(48), paragraph('REPORTED OBSERVATIONS', LABEL), paragraph(notes)])

    agency = route['jurisdiction']
    channel = route['destination_name']
    destination = [paragraph('REPORTING DESTINATION', LABEL), paragraph(channel, LOCATION)]
    if agency and agency != channel:
        destination.append(paragraph(agency, DETAIL))
    portal = route['portal_url']
    if portal:
        host = urlsplit(portal).netloc
        destination.append(Paragraph(
            f'Open reporting portal: <link href={quoteattr(portal)} color="#173F35">'
            f'<u>{escape(host)}</u></link>', DETAIL))
    if guidance := route.get('guidance'):
        destination.append(paragraph(guidance, DETAIL))
    story.extend([Spacer(1, 13), KeepTogether(destination)])

    output = BytesIO()
    doc = BaseDocTemplate(output, pagesize=letter, title=title, author='CivicFix',
                          pageCompression=1)
    frame = Frame(MARGIN, 57, BODY_WIDTH, PAGE_HEIGHT - 57 - 79,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='report', frames=[frame], onPage=page_details))
    doc.build(story)
    return output.getvalue()
