"""
build.py — Generador estático del directorio Anh Ngữ Việt Nam
────────────────────────────────────────────────────────────
Lee data.json y produce:
  - /trung-tam/{slug}.html      (108 fichas)
  - /danh-muc/{slug}.html       (11 categorías)
  - /danh-muc/index.html        (index de categorías)
  - /thanh-pho/{slug}.html      (3 ciudades)
  - /index.html                 (home)
  - /sitemap.xml
  - /robots.txt
  - /404.html
"""
import json, os, sys, html, re
from datetime import date
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_partials import (SITE, meta_head, header_html, footer_html,
                            mobile_toggle_script, stars_html)

SRC     = os.path.dirname(os.path.abspath(__file__))
OUT     = os.path.dirname(os.path.abspath(__file__))
DATA    = os.path.join(SRC, 'data.json')

# ────────────────────────────────────────────────────────────────────
# UTILIDADES
# ────────────────────────────────────────────────────────────────────
def esc(s):
    """HTML-escape seguro"""
    return html.escape(str(s or ''), quote=True)

def trunc(s, n=155):
    """Truncar preservando palabras, para meta description"""
    s = (s or '').strip()
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(' ', 1)[0]
    return cut + '…'

def img_tag(center, cls='', width=408, height=272, loading='lazy', fetch=None):
    """<img> accesible. Si no hay imagen, div placeholder."""
    if center.get('image'):
        fetch_attr = f' fetchpriority="{fetch}"' if fetch else ''
        alt = f"{center['name']} — {center.get('category_primary','Trung tâm Anh ngữ')} tại {center.get('city','Việt Nam')}"
        return (f'<img src="{esc(center["image"])}" alt="{esc(alt)}" '
                f'class="{cls}" width="{width}" height="{height}" '
                f'loading="{loading}" decoding="async"{fetch_attr}>')
    # Placeholder con data-city para que CSS aplique gradiente por ciudad
    city_slug = center.get('city_slug', '')
    return f'<div class="{cls} card-image-placeholder" data-city="{esc(city_slug)}" role="img" aria-label="Sin imagen disponible"></div>'


def render_star_number(rating, reviews_count):
    """Renderiza rating visual + número"""
    if not rating:
        return '<span class="card-no-rating">Chưa có đánh giá</span>'
    stars = stars_html(rating)
    return (f'<div class="card-rating">{stars}'
            f'<span class="score">{rating}</span>'
            f'<span class="reviews">({reviews_count or 0})</span></div>')


def card_html(center, base='../'):
    """Renderiza card de un centro"""
    url = f"{base}trung-tam/{center['slug']}.html"
    img = img_tag(center, cls='card-image')
    badge = f'<span class="card-badge">{esc(center.get("category_primary",""))}</span>' if center.get('category_primary') else ''
    rating = render_star_number(center.get('rating'), center.get('reviews_count'))
    return f'''<a class="center-card" href="{url}" aria-label="{esc(center['name'])} — xem hồ sơ chi tiết">
        <div class="card-image-wrapper">{img}{badge}</div>
        <div class="card-content">
          <h3 class="card-title">{esc(center['name'])}</h3>
          <p class="card-address">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {esc(center.get('address') or center.get('city') or 'Việt Nam')}
          </p>
          {rating}
          <span class="card-cta">Xem hồ sơ →</span>
        </div>
      </a>'''


# ────────────────────────────────────────────────────────────────────
# FICHAS (/trung-tam/{slug}.html)
# ────────────────────────────────────────────────────────────────────
def build_ficha(center, data):
    slug = center['slug']
    name = center['name']
    cat  = center.get('category_primary', 'Trung tâm')
    city = center.get('city', 'Việt Nam')
    rating = center.get('rating')
    reviews = center.get('reviews_count', 0)

    title = f'{name} — {cat} tại {city} | Anh Ngữ Việt Nam'
    desc_parts = [f'{name} tại {city}.']
    if center.get('address'): desc_parts.append(f'Địa chỉ: {center["address"]}.')
    if rating: desc_parts.append(f'Đánh giá {rating}/5 ({reviews} nhận xét).')
    if center.get('phone'): desc_parts.append(f'Điện thoại: {center["phone"]}.')
    description = trunc(' '.join(desc_parts), 155)

    canonical = f'/trung-tam/{slug}.html'
    og_image = center.get('image') or SITE['og_image']

    # Schema LocalBusiness completo
    schema = {
        '@context': 'https://schema.org',
        '@type': 'EducationalOrganization',
        '@id': SITE['domain'] + canonical + '#org',
        'name': name,
        'url': SITE['domain'] + canonical,
        'description': desc_parts[0],
    }
    if center.get('image'): schema['image'] = center['image']
    if center.get('phone'): schema['telephone'] = center['phone']
    if center.get('website'): schema['sameAs'] = [center['website']]
    if center.get('address'):
        schema['address'] = {
            '@type': 'PostalAddress',
            'streetAddress': center['address'],
            'addressLocality': city,
            'addressCountry': 'VN'
        }
    if center.get('geo', {}).get('lat'):
        schema['geo'] = {
            '@type': 'GeoCoordinates',
            'latitude': center['geo']['lat'],
            'longitude': center['geo']['lng']
        }
    if rating and reviews:
        schema['aggregateRating'] = {
            '@type': 'AggregateRating',
            'ratingValue': rating,
            'reviewCount': reviews,
            'bestRating': 5,
            'worstRating': 1
        }
    # BreadcrumbList schema
    bc_schema = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type':'ListItem','position':1,'name':'Trang chủ','item': SITE['domain'] + '/'},
            {'@type':'ListItem','position':2,'name':'Tất cả danh mục','item': SITE['domain'] + '/danh-muc/'},
            {'@type':'ListItem','position':3,'name':cat,'item': SITE['domain'] + f'/danh-muc/{center.get("category_slug","")}.html'},
            {'@type':'ListItem','position':4,'name':name,'item': SITE['domain'] + canonical},
        ]
    }

    # FAQ schema (si inventamos FAQs útiles)
    faqs = generate_faqs(center)
    faq_schema = None
    if faqs:
        faq_schema = {
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            'mainEntity': [
                {'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}}
                for q,a in faqs
            ]
        }

    # Related centers (misma categoría o ciudad, excluyendo él mismo)
    related = [c for c in data['centers']
               if c['slug'] != slug and
               (c.get('city_slug') == center.get('city_slug') or
                c.get('category_slug') == center.get('category_slug'))]
    # Priorizar misma ciudad + misma categoría
    related.sort(key=lambda c: (
        c.get('city_slug') != center.get('city_slug'),
        c.get('category_slug') != center.get('category_slug'),
        -(c.get('rating') or 0)
    ))
    related = related[:6]

    # ── HERO con imagen ──
    hero_img_html = ''
    if center.get('image'):
        alt = f'{name} — Ảnh đại diện'
        hero_img_html = f'<img src="{esc(center["image"])}" alt="{esc(alt)}" class="ficha-hero-img" width="600" height="400" fetchpriority="high" decoding="async">'
    else:
        hero_img_html = f'<div class="ficha-hero-img ficha-hero-placeholder" data-city="{esc(center.get("city_slug",""))}"></div>'

    # Rating bar
    if rating:
        stars = stars_html(rating)
        rating_bar = f'''<div class="ficha-rating-bar">
          <div class="rating-big">{rating}</div>
          <div class="rating-meta">
            {stars}
            <div class="rating-count"><strong>{reviews}</strong> nhận xét từ học viên</div>
          </div>
        </div>'''
    else:
        rating_bar = '<div class="ficha-rating-bar"><div class="rating-none">Chưa có đánh giá</div></div>'

    # CTAs (hero)
    ctas = []
    if center.get('phone'):
        ctas.append(f'<a href="tel:{esc(center["phone"])}" class="btn btn-call" data-action="call"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.86 19.86 0 01-8.63-3.15A19.5 19.5 0 014.23 11.83 19.86 19.86 0 011.05 3.55A2 2 0 013 1.36h3a2 2 0 012 1.72c.11.81.29 1.61.55 2.39a2 2 0 01-.45 2L6.24 8.24a16 16 0 007.52 7.52l1.38-1.38a2 2 0 012-.45c.78.26 1.58.44 2.39.55a2 2 0 011.72 2z"/></svg> Gọi: {esc(center["phone"])}</a>')
    if center.get('website'):
        w = center['website'] if center['website'].startswith('http') else 'http://'+center['website']
        ctas.append(f'<a href="{esc(w)}" class="btn btn-website" target="_blank" rel="noopener noreferrer" data-action="website"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg> Website chính thức</a>')
    if center.get('geo', {}).get('lat'):
        ctas.append(f'<a href="https://www.google.com/maps/dir/?api=1&destination={center["geo"]["lat"]},{center["geo"]["lng"]}" class="btn btn-directions" target="_blank" rel="noopener noreferrer" data-action="directions"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg> Chỉ đường</a>')
    ctas_html = ''.join(ctas)

    # Info sections
    sections = []

    # Servicios
    if center.get('services'):
        srv = ''.join(f'<li>{esc(s)}</li>' for s in center['services'])
        sections.append(f'<div class="detail-section"><h2 class="detail-h"><span class="icon" aria-hidden="true">🎯</span>Dịch vụ giảng dạy</h2><ul class="services-list">{srv}</ul></div>')

    # Información de contacto detallada
    contact_rows = []
    if center.get('address'):
        contact_rows.append(f'<div class="contact-row"><span class="contact-label">Địa chỉ</span><span class="contact-value">{esc(center["address"])}</span></div>')
    if center.get('phone'):
        contact_rows.append(f'<div class="contact-row"><span class="contact-label">Điện thoại</span><a class="contact-value contact-link" href="tel:{esc(center["phone"])}">{esc(center["phone"])}</a></div>')
    if center.get('website'):
        w = center['website'] if center['website'].startswith('http') else 'http://'+center['website']
        contact_rows.append(f'<div class="contact-row"><span class="contact-label">Website</span><a class="contact-value contact-link" href="{esc(w)}" target="_blank" rel="noopener noreferrer">{esc(center["website"])}</a></div>')
    if contact_rows:
        sections.append(f'<div class="detail-section"><h2 class="detail-h"><span class="icon" aria-hidden="true">📍</span>Thông tin liên hệ</h2><div class="contact-rows">{"".join(contact_rows)}</div></div>')

    # Mapa
    if center.get('maps_iframe'):
        mi = center['maps_iframe'].strip()
        # El campo puede venir como iframe HTML completo o como URL. Normalizar.
        if mi.startswith('<iframe'):
            iframe = mi
            if 'loading=' not in iframe:
                iframe = iframe.replace('<iframe', '<iframe loading="lazy"', 1)
        elif mi.startswith('http'):
            # URL sola: envolver en iframe
            iframe = f'<iframe src="{esc(mi)}" width="100%" height="400" style="border:0" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Bản đồ {esc(name)}" allowfullscreen></iframe>'
        else:
            iframe = ''
        if iframe:
            sections.append(f'<div class="detail-section"><h2 class="detail-h"><span class="icon" aria-hidden="true">🗺️</span>Vị trí trên bản đồ</h2><div class="map-wrapper">{iframe}</div></div>')
    elif center.get('geo', {}).get('lat'):
        lat, lng = center['geo']['lat'], center['geo']['lng']
        iframe_url = f'https://www.google.com/maps/embed/v1/place?key=&q={lat},{lng}'
        iframe = f'<iframe src="https://maps.google.com/maps?q={lat},{lng}&z=15&output=embed" width="100%" height="400" style="border:0" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Bản đồ {esc(name)}"></iframe>'
        sections.append(f'<div class="detail-section"><h2 class="detail-h"><span class="icon" aria-hidden="true">🗺️</span>Vị trí trên bản đồ</h2><div class="map-wrapper">{iframe}</div></div>')

    # FAQs
    if faqs:
        faq_items = ''
        for q, a in faqs:
            faq_items += f'''<details class="faq-item"><summary class="faq-q">{esc(q)}<span class="faq-icon" aria-hidden="true">+</span></summary><div class="faq-a">{esc(a)}</div></details>'''
        sections.append(f'<div class="detail-section"><h2 class="detail-h"><span class="icon" aria-hidden="true">❓</span>Câu hỏi thường gặp</h2><div class="faq-list">{faq_items}</div></div>')

    sections_html = ''.join(sections)

    # Related cards
    related_html = ''
    if related:
        cards = ''.join(card_html(c, base='../') for c in related)
        related_html = f'''<section class="related-section">
        <div class="container">
          <div class="section-header">
            <div class="section-label">Gợi ý khác</div>
            <h2 class="section-title">Trung tâm liên quan</h2>
          </div>
          <div class="centers-grid">{cards}</div>
        </div>
      </section>'''

    # Breadcrumbs visuales
    bc_html = f'''<nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="../">Trang chủ</a>
        <span class="sep" aria-hidden="true">›</span>
        <a href="../danh-muc/">Danh mục</a>
        <span class="sep" aria-hidden="true">›</span>
        <a href="../danh-muc/{esc(center.get("category_slug","trung-tam-anh-ngu"))}.html">{esc(cat)}</a>
        <span class="sep" aria-hidden="true">›</span>
        <span class="current" aria-current="page">{esc(name)}</span>
      </nav>'''

    schemas = [schema, bc_schema]
    if faq_schema: schemas.append(faq_schema)
    schema_tags = '\n'.join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>'
                            for s in schemas)

    head = meta_head(title, description, canonical, og_image=og_image).format(css_path='../')

    body = f'''<!DOCTYPE html>
<html lang="{SITE['lang']}">
<head>
{head}
{schema_tags}
</head>
<body class="page-ficha">
{header_html(base='../')}
<main id="main">
  <section class="ficha-hero">
    <div class="container ficha-hero-inner">
      <div class="ficha-hero-media">{hero_img_html}</div>
      <div class="ficha-hero-body">
        {bc_html}
        <div class="hero-cat-eyebrow">{esc(cat)}</div>
        <h1 class="ficha-h1">{esc(name)}</h1>
        <p class="ficha-intro">{esc(desc_parts[0])} {esc("Đầy đủ thông tin liên hệ, đánh giá và dịch vụ giảng dạy.")}</p>
        {rating_bar}
        <div class="ficha-ctas">{ctas_html}</div>
      </div>
    </div>
  </section>

  <section class="section-details">
    <div class="container details-container">
      {sections_html}
    </div>
  </section>
  {related_html}
</main>
{footer_html(base='../')}
<script src="../popup.js" defer></script>
{mobile_toggle_script()}
</body>
</html>'''
    path = os.path.join(OUT, 'trung-tam', f'{slug}.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(body)


def generate_faqs(center):
    """FAQs útiles por centro"""
    faqs = []
    name = center['name']
    city = center.get('city', 'Việt Nam')
    cat = center.get('category_primary', 'Trung tâm Anh ngữ')

    if center.get('address'):
        faqs.append((f'{name} nằm ở đâu?',
                     f'{name} có địa chỉ tại {center["address"]}.'))
    if center.get('phone'):
        faqs.append((f'Làm thế nào để liên hệ {name}?',
                     f'Bạn có thể gọi điện qua số {center["phone"]}' +
                     (f' hoặc truy cập website {center["website"]}.' if center.get('website') else '.')))
    if center.get('rating') and center.get('reviews_count'):
        faqs.append((f'{name} có tốt không?',
                     f'{name} hiện có điểm đánh giá trung bình {center["rating"]}/5 dựa trên {center["reviews_count"]} nhận xét từ học viên thực tế trên Google.'))
    if center.get('services'):
        srvs = ', '.join(center['services'][:5])
        faqs.append((f'{name} cung cấp những dịch vụ gì?',
                     f'{name} cung cấp các dịch vụ: {srvs}.'))
    faqs.append((f'{name} có phải là lựa chọn tốt tại {city} không?',
                 f'{name} là một {cat.lower()} tại {city}. Hãy tham khảo đánh giá từ học viên và so sánh với các trung tâm tương tự trong danh bạ của chúng tôi trước khi quyết định.'))
    return faqs[:5]


# ────────────────────────────────────────────────────────────────────
# CATEGORÍAS (/danh-muc/{slug}.html)
# ────────────────────────────────────────────────────────────────────
CATEGORY_META = {
    "trung-tam-anh-ngu": {
        "h1": "Trung tâm Anh ngữ tại Việt Nam",
        "intro": "Danh sách đầy đủ các trung tâm Anh ngữ uy tín tại Hồ Chí Minh, Đà Nẵng và Hà Nội. So sánh đánh giá, dịch vụ và vị trí để tìm nơi học phù hợp nhất.",
        "content": "Các trung tâm Anh ngữ tại Việt Nam cung cấp đa dạng khóa học từ giao tiếp cơ bản đến luyện thi IELTS, TOEIC chuyên sâu. Khi lựa chọn, hãy cân nhắc kinh nghiệm giảng viên, phương pháp giảng dạy, vị trí thuận tiện và đánh giá thực tế từ học viên."
    },
    "trung-tam-ngoai-ngu": {
        "h1": "Trung tâm ngoại ngữ tại Việt Nam",
        "intro": "Các trung tâm ngoại ngữ dạy tiếng Anh và nhiều ngôn ngữ khác tại Việt Nam.",
        "content": "Nhiều trung tâm ngoại ngữ tại Việt Nam cung cấp chương trình đào tạo đa ngôn ngữ — từ tiếng Anh, tiếng Pháp, tiếng Trung đến tiếng Nhật và Hàn. Đây là lựa chọn lý tưởng cho người muốn mở rộng cơ hội nghề nghiệp trong bối cảnh hội nhập quốc tế."
    },
    "trung-tam-giao-duc": {
        "h1": "Trung tâm giáo dục tại Việt Nam",
        "intro": "Các trung tâm giáo dục uy tín dạy tiếng Anh chất lượng cao.",
        "content": "Các trung tâm giáo dục tại Việt Nam cung cấp môi trường học tập chuyên nghiệp với chương trình được thiết kế phù hợp cho nhiều đối tượng, từ trẻ em đến người trưởng thành."
    },
    "co-so-giao-duc": {
        "h1": "Cơ sở giáo dục Anh ngữ tại Việt Nam",
        "intro": "Danh sách cơ sở giáo dục dạy tiếng Anh được đánh giá cao.",
        "content": "Các cơ sở giáo dục trong danh bạ đã được kiểm chứng qua đánh giá của học viên thực tế, đảm bảo chất lượng giảng dạy và dịch vụ hỗ trợ học tập."
    },
    "trung-tam-dao-tao": {
        "h1": "Trung tâm đào tạo tiếng Anh tại Việt Nam",
        "intro": "Trung tâm đào tạo chuyên sâu với chứng chỉ quốc tế.",
        "content": "Các trung tâm đào tạo tập trung vào phát triển kỹ năng chuyên sâu với chương trình cấp chứng chỉ được công nhận quốc tế như TESOL, TEFL hoặc Cambridge."
    },
    "trung-tam-hoc-tap": {
        "h1": "Trung tâm học tập tiếng Anh",
        "intro": "Môi trường học tập tiếng Anh cho mọi lứa tuổi.",
        "content": "Môi trường học tập thân thiện, phù hợp cho cả trẻ em lẫn người lớn, với phương pháp giảng dạy hiện đại và tương tác."
    },
    "trung-tam-dao-tao-nghe": {
        "h1": "Trung tâm đào tạo nghề — Anh ngữ chuyên ngành",
        "intro": "Đào tạo tiếng Anh chuyên ngành cho người đi làm.",
        "content": "Các trung tâm đào tạo nghề cung cấp chương trình tiếng Anh chuyên ngành — nhà hàng, khách sạn, du lịch, kinh doanh — phù hợp cho người đã đi làm muốn nâng cao kỹ năng."
    },
    "trung-tam-mam-non": {
        "h1": "Trung tâm mầm non — Tiếng Anh cho trẻ nhỏ",
        "intro": "Tiếng Anh cho trẻ em từ lứa tuổi mầm non.",
        "content": "Các trung tâm mầm non dạy tiếng Anh tập trung vào phương pháp học qua trò chơi, hoạt động sáng tạo — giúp trẻ tiếp thu ngôn ngữ tự nhiên trong giai đoạn vàng."
    },
    "dai-hoc": {
        "h1": "Khóa học Anh ngữ tại Đại học",
        "intro": "Chương trình tiếng Anh tại các trường đại học.",
        "content": "Nhiều trường đại học tại Việt Nam cung cấp các khóa học tiếng Anh bên ngoài chương trình chính quy — đặc biệt phù hợp cho sinh viên muốn nâng cao kỹ năng."
    },
    "van-phong-cong-ty": {
        "h1": "Anh ngữ tại văn phòng công ty",
        "intro": "Trung tâm Anh ngữ tổ chức dạy tại công ty.",
        "content": "Dịch vụ đào tạo tiếng Anh tại chỗ cho doanh nghiệp — linh hoạt về lịch học, tập trung vào tiếng Anh thương mại và giao tiếp chuyên nghiệp."
    },
    "trung-tam-luyen-thi": {
        "h1": "Trung tâm luyện thi tiếng Anh — IELTS, TOEIC",
        "intro": "Luyện thi IELTS, TOEIC và các chứng chỉ quốc tế.",
        "content": "Trung tâm luyện thi chuyên biệt với giáo viên có kinh nghiệm và tài liệu cập nhật theo cấu trúc đề thi mới nhất. Lý tưởng cho mục tiêu du học, làm việc quốc tế."
    },
}


def build_category(cat, data):
    slug = cat['slug']
    name = cat['name']
    meta = CATEGORY_META.get(slug, {
        'h1': name, 'intro': f'Các {name.lower()} tại Việt Nam.',
        'content': f'Danh sách đầy đủ các {name.lower()} tại Việt Nam.'
    })
    centers_in_cat = [c for c in data['centers'] if c.get('category_slug') == slug]

    title = f'{meta["h1"]} | Top {len(centers_in_cat)} lựa chọn 2026'
    description = trunc(meta['intro'], 155)
    canonical = f'/danh-muc/{slug}.html'

    cards = ''.join(card_html(c, base='../') for c in centers_in_cat)

    # Ciudades
    cities_in_cat = {}
    for c in centers_in_cat:
        cs = c.get('city_slug','')
        cn = c.get('city','')
        cities_in_cat[cs] = (cn, cities_in_cat.get(cs, (cn,0))[1] + 1)

    cities_html = ''
    for cs, (cn, n) in cities_in_cat.items():
        cities_html += f'<a href="../thanh-pho/{cs}.html" class="city-chip">{esc(cn)} <span class="city-count">({n})</span></a>'

    # Schema CollectionPage + ItemList
    items = [
        {
            '@type':'ListItem','position':i+1,
            'item':{
                '@type':'EducationalOrganization',
                'name':c['name'],
                'url': SITE['domain'] + f'/trung-tam/{c["slug"]}.html',
                **({'image': c['image']} if c.get('image') else {}),
                **({'aggregateRating':{'@type':'AggregateRating','ratingValue':c['rating'],'reviewCount':c.get('reviews_count',0)}} if c.get('rating') else {})
            }
        } for i, c in enumerate(centers_in_cat[:30])
    ]
    schema = {
        '@context':'https://schema.org',
        '@type':'CollectionPage',
        'name': meta['h1'],
        'description': meta['intro'],
        'url': SITE['domain'] + canonical,
        'mainEntity': {'@type':'ItemList','numberOfItems':len(centers_in_cat),'itemListElement': items}
    }
    bc_schema = {
        '@context':'https://schema.org','@type':'BreadcrumbList',
        'itemListElement':[
            {'@type':'ListItem','position':1,'name':'Trang chủ','item':SITE['domain']+'/'},
            {'@type':'ListItem','position':2,'name':'Tất cả danh mục','item':SITE['domain']+'/danh-muc/'},
            {'@type':'ListItem','position':3,'name':name,'item':SITE['domain']+canonical},
        ]
    }

    head = meta_head(title, description, canonical).format(css_path='../')

    body = f'''<!DOCTYPE html>
<html lang="{SITE['lang']}">
<head>
{head}
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc_schema, ensure_ascii=False)}</script>
</head>
<body class="page-category">
{header_html(base='../')}
<main id="main">
  <section class="hero category">
    <div class="hero-grid" aria-hidden="true"></div>
    <div class="container">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="../">Trang chủ</a>
        <span class="sep" aria-hidden="true">›</span>
        <a href="./">Danh mục</a>
        <span class="sep" aria-hidden="true">›</span>
        <span class="current" aria-current="page">{esc(name)}</span>
      </nav>
      <div class="hero-cat-eyebrow">Danh mục</div>
      <h1 class="category-h1">{esc(meta["h1"])}</h1>
      <p class="cat-intro">{esc(meta["intro"])}</p>
      <div class="cat-stats-bar">
        <div class="cat-stat"><strong>{len(centers_in_cat)}</strong> trung tâm</div>
      </div>
    </div>
  </section>

  <section class="section-listing">
    <div class="container">
      {f'<div class="city-filter-bar"><span class="filter-label">Thành phố:</span>{cities_html}</div>' if cities_html else ''}
      <div class="centers-grid">
        {cards}
      </div>
    </div>
  </section>

  <section class="seo-section">
    <div class="container seo-inner">
      <h2>Về {esc(name.lower())} tại Việt Nam</h2>
      <p>{esc(meta["content"])}</p>
    </div>
  </section>
</main>
{footer_html(base='../')}
<script src="../popup.js" defer></script>
{mobile_toggle_script()}
</body>
</html>'''
    path = os.path.join(OUT, 'danh-muc', f'{slug}.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(body)


def build_category_index(data):
    """/danh-muc/index.html — Lista de todas las categorías"""
    title = 'Tất cả danh mục trung tâm Anh ngữ | Anh Ngữ Việt Nam'
    description = 'Khám phá trung tâm Anh ngữ theo danh mục: luyện thi IELTS, TOEIC, trẻ em, giao tiếp. Tìm loại hình học phù hợp với bạn.'
    canonical = '/danh-muc/'

    cats_html = ''
    for cat in data['categories']:
        n = len([c for c in data['centers'] if c.get('category_slug') == cat['slug']])
        if n == 0: continue
        meta = CATEGORY_META.get(cat['slug'], {})
        intro = meta.get('intro', '')
        cats_html += f'''<a href="{cat["slug"]}.html" class="category-card-big">
          <div class="cat-icon" aria-hidden="true">{cat.get("icon","📚")}</div>
          <div class="cat-body">
            <h2 class="cat-name">{esc(cat["name"])}</h2>
            <p class="cat-desc">{esc(intro)}</p>
            <div class="cat-count"><strong>{n}</strong> trung tâm</div>
          </div>
          <div class="cat-arrow" aria-hidden="true">→</div>
        </a>'''

    head = meta_head(title, description, canonical).format(css_path='../')

    body = f'''<!DOCTYPE html>
<html lang="{SITE['lang']}">
<head>
{head}
</head>
<body class="page-category-index">
{header_html(base='../')}
<main id="main">
  <section class="hero category">
    <div class="hero-grid" aria-hidden="true"></div>
    <div class="container">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="../">Trang chủ</a>
        <span class="sep" aria-hidden="true">›</span>
        <span class="current" aria-current="page">Danh mục</span>
      </nav>
      <h1 class="category-h1">Tất cả danh mục</h1>
      <p class="cat-intro">Chọn loại hình trung tâm phù hợp với mục tiêu học của bạn.</p>
    </div>
  </section>
  <section class="section-listing">
    <div class="container">
      <div class="categories-list-big">{cats_html}</div>
    </div>
  </section>
</main>
{footer_html(base='../')}
<script src="../popup.js" defer></script>
{mobile_toggle_script()}
</body>
</html>'''
    with open(os.path.join(OUT, 'danh-muc', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(body)


# ────────────────────────────────────────────────────────────────────
# CIUDADES
# ────────────────────────────────────────────────────────────────────
CITY_META = {
    'ho-chi-minh': {
        'name_full': 'Hồ Chí Minh', 'h1': 'Trung tâm Anh ngữ tại Hồ Chí Minh',
        'intro': 'Tổng hợp các trung tâm Anh ngữ tốt nhất tại TP.HCM — từ quận 1 trung tâm đến các quận vệ tinh. So sánh đánh giá và chọn nơi học phù hợp.',
        'content': 'Hồ Chí Minh là thành phố có số lượng trung tâm Anh ngữ đa dạng nhất Việt Nam, trải dài từ các thương hiệu quốc tế đến trung tâm địa phương chuyên biệt. Các khu vực tập trung nhiều trung tâm chất lượng bao gồm quận 1, quận 3, quận 7 và Thủ Đức.'
    },
    'da-nang': {
        'name_full': 'Đà Nẵng', 'h1': 'Trung tâm Anh ngữ tại Đà Nẵng',
        'intro': 'Các trung tâm Anh ngữ uy tín tại Đà Nẵng — điểm đến học tiếng Anh phát triển nhanh nhất miền Trung.',
        'content': 'Đà Nẵng đang nhanh chóng trở thành một trong những điểm đến học tiếng Anh phát triển nhất miền Trung. Nhiều trung tâm tập trung tại các quận Hải Châu, Thanh Khê và Sơn Trà, đáp ứng nhu cầu học từ trẻ em đến luyện thi IELTS chuyên sâu.'
    },
    'ha-noi': {
        'name_full': 'Hà Nội', 'h1': 'Trung tâm Anh ngữ tại Hà Nội',
        'intro': 'Các trung tâm Anh ngữ chất lượng tại thủ đô — đánh giá, vị trí, giá học phí.',
        'content': 'Hà Nội là trung tâm giáo dục lớn thứ hai cả nước, với nhiều trung tâm Anh ngữ uy tín lâu đời. Các khu vực Cầu Giấy, Ba Đình và Đống Đa tập trung nhiều lựa chọn chất lượng cho cả học viên cá nhân và doanh nghiệp.'
    },
}


def build_city(city, data):
    slug = city['slug']
    meta = CITY_META.get(slug, {'name_full': city['name'], 'h1': f'Trung tâm Anh ngữ tại {city["name"]}',
                                 'intro': f'Các trung tâm Anh ngữ tại {city["name"]}.',
                                 'content': f'Danh sách trung tâm tại {city["name"]}.'})
    centers = [c for c in data['centers'] if c.get('city_slug') == slug]

    title = f'{meta["h1"]} | Top {len(centers)} được yêu thích 2026'
    description = trunc(meta['intro'], 155)
    canonical = f'/thanh-pho/{slug}.html'

    cards = ''.join(card_html(c, base='../') for c in centers)

    # Categorías presentes
    cats_present = {}
    for c in centers:
        cs = c.get('category_slug',''); cn = c.get('category_primary','')
        if cs: cats_present[cs] = (cn, cats_present.get(cs,(cn,0))[1]+1)
    cats_html = ''
    for cs, (cn, n) in cats_present.items():
        cats_html += f'<a href="../danh-muc/{cs}.html" class="city-chip">{esc(cn)} <span class="city-count">({n})</span></a>'

    schema = {
        '@context':'https://schema.org','@type':'CollectionPage',
        'name': meta['h1'], 'description': meta['intro'],
        'url': SITE['domain'] + canonical,
    }
    bc_schema = {
        '@context':'https://schema.org','@type':'BreadcrumbList',
        'itemListElement':[
            {'@type':'ListItem','position':1,'name':'Trang chủ','item':SITE['domain']+'/'},
            {'@type':'ListItem','position':2,'name':meta['name_full'],'item':SITE['domain']+canonical},
        ]
    }

    head = meta_head(title, description, canonical).format(css_path='../')
    body = f'''<!DOCTYPE html>
<html lang="{SITE['lang']}">
<head>
{head}
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc_schema, ensure_ascii=False)}</script>
</head>
<body class="page-city">
{header_html(base='../')}
<main id="main">
  <section class="hero category" data-city="{slug}">
    <div class="hero-grid" aria-hidden="true"></div>
    <div class="container">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="../">Trang chủ</a>
        <span class="sep" aria-hidden="true">›</span>
        <span class="current" aria-current="page">{esc(meta["name_full"])}</span>
      </nav>
      <div class="hero-cat-eyebrow">Thành phố</div>
      <h1 class="category-h1">{esc(meta["h1"])}</h1>
      <p class="cat-intro">{esc(meta["intro"])}</p>
      <div class="cat-stats-bar">
        <div class="cat-stat"><strong>{len(centers)}</strong> trung tâm tại {esc(meta["name_full"])}</div>
      </div>
    </div>
  </section>
  <section class="section-listing">
    <div class="container">
      {f'<div class="city-filter-bar"><span class="filter-label">Loại hình:</span>{cats_html}</div>' if cats_html else ''}
      <div class="centers-grid">{cards}</div>
    </div>
  </section>
  <section class="seo-section">
    <div class="container seo-inner">
      <h2>Về việc học tiếng Anh tại {esc(meta["name_full"])}</h2>
      <p>{esc(meta["content"])}</p>
    </div>
  </section>
</main>
{footer_html(base='../')}
<script src="../popup.js" defer></script>
{mobile_toggle_script()}
</body>
</html>'''
    with open(os.path.join(OUT, 'thanh-pho', f'{slug}.html'), 'w', encoding='utf-8') as f:
        f.write(body)


# ────────────────────────────────────────────────────────────────────
# HOME
# ────────────────────────────────────────────────────────────────────
def build_home(data):
    title = f'Anh Ngữ Việt Nam | Danh bạ {len(data["centers"])} trung tâm Anh ngữ 2026'
    description = f'Tìm và so sánh {len(data["centers"])}+ trung tâm Anh ngữ tại Hồ Chí Minh, Đà Nẵng, Hà Nội. Đánh giá thực tế, thông tin chi tiết, liên hệ trực tiếp.'
    canonical = '/'

    # Top 6 centros
    top = sorted([c for c in data['centers'] if c.get('rating') and c.get('reviews_count')],
                 key=lambda c: (c['rating'], c['reviews_count']), reverse=True)[:6]
    top_cards = ''
    for i, c in enumerate(top):
        ctx = card_html(c, base='')
        # Primera con fetchpriority=high
        if i == 0 and c.get('image'):
            ctx = ctx.replace('loading="lazy"', 'loading="eager" fetchpriority="high"', 1)
        top_cards += ctx

    # Categorías
    cats_html = ''
    for cat in data['categories']:
        n = len([c for c in data['centers'] if c.get('category_slug') == cat['slug']])
        if n == 0: continue
        cats_html += f'''<a class="category-card" href="danh-muc/{cat["slug"]}.html">
          <div class="cat-icon" aria-hidden="true">{cat.get("icon","📚")}</div>
          <div class="cat-name">{esc(cat["name"])}</div>
          <div class="cat-count">{n} trung tâm</div>
          <div class="cat-arrow" aria-hidden="true">→</div>
        </a>'''

    # Ciudades
    cities_html = ''
    for city in data['cities']:
        n = len([c for c in data['centers'] if c.get('city_slug') == city['slug']])
        cities_html += f'<a href="thanh-pho/{city["slug"]}.html" class="city-chip">{esc(city["name"])} <span class="city-count">({n})</span></a>'

    # Schema WebSite + SearchAction + Organization
    schemas = [
        {
            '@context':'https://schema.org','@type':'WebSite',
            'name': SITE['name'], 'url': SITE['domain']+'/',
            'inLanguage':'vi',
            'potentialAction':{
                '@type':'SearchAction',
                'target':{'@type':'EntryPoint','urlTemplate':SITE['domain']+'/danh-muc/?search={search_term_string}'},
                'query-input':'required name=search_term_string'
            }
        },
        {
            '@context':'https://schema.org','@type':'Organization',
            'name': SITE['name'], 'url': SITE['domain']+'/',
        }
    ]
    schema_tags = '\n'.join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas)

    head = meta_head(title, description, canonical).format(css_path='')

    body = f'''<!DOCTYPE html>
<html lang="{SITE['lang']}">
<head>
{head}
{schema_tags}
</head>
<body class="page-home">
{header_html(base='')}
<main id="main">
  <section class="hero home">
    <div class="hero-grid" aria-hidden="true"></div>
    <div class="orb orb-1" aria-hidden="true"></div>
    <div class="orb orb-2" aria-hidden="true"></div>
    <div class="orb orb-3" aria-hidden="true"></div>
    <div class="container hero-content">
      <div class="hero-eyebrow"><span class="eyebrow-dot"></span>Nền tảng khám phá giáo dục số 1 Việt Nam</div>
      <h1 class="hero-title">Tìm trung tâm<br><span class="title-highlight">Anh ngữ</span> hoàn hảo<br>của bạn</h1>
      <p class="hero-subtitle">So sánh <strong>{len(data["centers"])} trung tâm</strong> Anh ngữ tại Hồ Chí Minh, Đà Nẵng và Hà Nội. Đánh giá thực tế, thông tin minh bạch.</p>
      <div class="stats-bar">
        <div class="stat-item"><strong>{len(data["centers"])}+</strong><span>Trung tâm</span></div>
        <div class="stat-sep"></div>
        <div class="stat-item"><strong>{len(data["cities"])}</strong><span>Thành phố</span></div>
        <div class="stat-sep"></div>
        <div class="stat-item"><strong>4.8★</strong><span>Đánh giá TB</span></div>
      </div>
      <form class="search-box" action="danh-muc/" method="get" role="search">
        <div class="search-field">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input type="search" name="search" placeholder="Tìm theo tên hoặc địa chỉ…" autocomplete="off" aria-label="Tìm kiếm trung tâm">
        </div>
        <button class="search-btn" type="submit">
          <span>Tìm kiếm</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </form>
      <div class="popular-tags">
        <span class="tags-label">Thành phố:</span>
        {cities_html}
      </div>
    </div>
  </section>

  <section class="section-categories">
    <div class="container">
      <div class="section-header">
        <div class="section-label">Danh mục</div>
        <h2 class="section-title">Khám phá theo<br>loại hình đào tạo</h2>
      </div>
      <div class="categories-grid">
        {cats_html}
      </div>
    </div>
  </section>

  <section class="section-top">
    <div class="container">
      <div class="section-header">
        <div class="section-label">Nổi bật</div>
        <h2 class="section-title">Trung tâm<br>hàng đầu</h2>
        <a href="danh-muc/" class="section-link">Xem tất cả →</a>
      </div>
      <div class="centers-grid">
        {top_cards}
      </div>
    </div>
  </section>

  <section class="seo-section">
    <div class="container seo-inner">
      <h2>Cẩm nang trung tâm Anh ngữ tại Việt Nam</h2>
      <p>Học tiếng Anh tại Việt Nam chưa bao giờ có nhiều lựa chọn đến thế. Từ các trung tâm quốc tế lớn đến các cơ sở địa phương chuyên biệt, danh bạ của chúng tôi tổng hợp <strong>{len(data["centers"])} trung tâm</strong> trên 3 thành phố lớn — Hồ Chí Minh, Đà Nẵng và Hà Nội.</p>
      <p>Mỗi trung tâm đều có thông tin chi tiết về vị trí, số điện thoại, website, dịch vụ giảng dạy và đánh giá thực tế từ học viên trên Google. Bạn có thể lọc theo <a href="danh-muc/trung-tam-luyen-thi.html">trung tâm luyện thi IELTS/TOEIC</a>, <a href="danh-muc/trung-tam-mam-non.html">trung tâm cho trẻ em</a>, hoặc <a href="danh-muc/van-phong-cong-ty.html">đào tạo tại doanh nghiệp</a>.</p>
    </div>
  </section>
</main>
{footer_html(base='')}
<script src="popup.js" defer></script>
{mobile_toggle_script()}
</body>
</html>'''
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(body)


# ────────────────────────────────────────────────────────────────────
# SITEMAP + ROBOTS + 404
# ────────────────────────────────────────────────────────────────────
def build_sitemap(data):
    today = date.today().isoformat()
    urls = [
        (SITE['domain']+'/', '1.0', 'weekly'),
        (SITE['domain']+'/danh-muc/', '0.9', 'weekly'),
    ]
    for cat in data['categories']:
        n = len([c for c in data['centers'] if c.get('category_slug')==cat['slug']])
        if n:
            urls.append((SITE['domain']+f'/danh-muc/{cat["slug"]}.html', '0.8', 'weekly'))
    for city in data['cities']:
        urls.append((SITE['domain']+f'/thanh-pho/{city["slug"]}.html', '0.8', 'weekly'))
    for c in data['centers']:
        urls.append((SITE['domain']+f'/trung-tam/{c["slug"]}.html', '0.7', 'monthly'))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pri, freq in urls:
        xml.append(f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>{freq}</changefreq><priority>{pri}</priority></url>')
    xml.append('</urlset>')
    with open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml))


def build_robots():
    txt = f'''User-agent: *
Allow: /
Disallow: /*.json$

Sitemap: {SITE["domain"]}/sitemap.xml
'''
    with open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(txt)


def build_404():
    head = meta_head('404 - Không tìm thấy trang',
                     'Trang bạn đang tìm không tồn tại. Quay lại trang chủ để khám phá danh bạ trung tâm Anh ngữ.',
                     '/404.html', noindex=True).format(css_path='')
    body = f'''<!DOCTYPE html>
<html lang="{SITE['lang']}">
<head>{head}</head>
<body class="page-404">
{header_html(base='')}
<main id="main">
  <section class="hero home" style="min-height:60vh">
    <div class="container hero-content" style="text-align:center">
      <h1 class="hero-title" style="font-size:4rem">404</h1>
      <p class="hero-subtitle">Trang bạn đang tìm không tồn tại hoặc đã bị di chuyển.</p>
      <a href="/" class="btn btn-primary" style="display:inline-flex;margin-top:24px">← Về trang chủ</a>
    </div>
  </section>
</main>
{footer_html(base='')}
{mobile_toggle_script()}
</body>
</html>'''
    with open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8') as f:
        f.write(body)


# ────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────
def main():
    with open(DATA, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, 'trung-tam'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'danh-muc'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'thanh-pho'), exist_ok=True)

    print(f'Build sitio: {len(data["centers"])} centros, {len(data["categories"])} cat, {len(data["cities"])} ciudades')

    # Home
    build_home(data); print('  ✓ index.html')
    # Categorías
    build_category_index(data); print('  ✓ danh-muc/index.html')
    for cat in data['categories']:
        n = len([c for c in data['centers'] if c.get('category_slug')==cat['slug']])
        if n: build_category(cat, data)
    print(f'  ✓ danh-muc/*.html ({len([c for c in data["categories"] if len([x for x in data["centers"] if x.get("category_slug")==c["slug"]])])})')
    # Ciudades
    for city in data['cities']:
        build_city(city, data)
    print(f'  ✓ thanh-pho/*.html ({len(data["cities"])})')
    # Fichas
    for c in data['centers']:
        build_ficha(c, data)
    print(f'  ✓ trung-tam/*.html ({len(data["centers"])})')
    # Extras
    build_sitemap(data); print('  ✓ sitemap.xml')
    build_robots(); print('  ✓ robots.txt')
    build_404(); print('  ✓ 404.html')
    print('Done.')


if __name__ == '__main__':
    main()
