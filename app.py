
from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, re, os, json, time, math
from xml.etree import ElementTree as ET

app = Flask(__name__)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 Chrome/127 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language":"en-US,en;q=0.9"}

SOCIAL_DOMAINS = {
    "LinkedIn":["linkedin.com/company/"],
    "Instagram":["instagram.com/"],
    "Facebook":["facebook.com/","fb.com/"],
    "YouTube":["youtube.com/","youtu.be/"],
    "TikTok":["tiktok.com/@"],
    "X":["x.com/","twitter.com/"]
}

TECH_PATTERNS = {
    "Google Analytics":[r"google-analytics\.com",r"googletagmanager\.com/gtag",r"\bG-[A-Z0-9]{5,}"],
    "Google Tag Manager":[r"googletagmanager\.com/gtm\.js",r"\bGTM-[A-Z0-9]+"],
    "Google Ads":[r"googleadservices\.com",r"\bAW-\d+"],
    "Meta Pixel":[r"connect\.facebook\.net",r"\bfbq\("],
    "LinkedIn Insight":[r"snap\.licdn\.com",r"_linkedin_partner_id"],
    "TikTok Pixel":[r"analytics\.tiktok\.com",r"ttq\."],
    "Microsoft Clarity":[r"clarity\.ms",r"\bclarity\("],
    "Hotjar":[r"hotjar\.com",r"\bhj\("],
    "HubSpot":[r"js\.hs-scripts\.com",r"hubspot"],
    "Marketo":[r"munchkin\.marketo\.net",r"marketo"],
    "Pardot / Account Engagement":[r"pardot"],
    "Salesforce":[r"salesforce"],
    "Segment":[r"cdn\.segment\.com",r"analytics\.load\("],
    "Intercom":[r"intercom"],
    "Drift":[r"drift\.com",r"driftt"],
    "Calendly":[r"calendly\.com"],
    "Chili Piper":[r"chilipiper"],
    "Webflow":[r"webflow"],
    "WordPress":[r"wp-content",r"wp-includes"],
    "Shopify":[r"cdn\.shopify\.com",r"shopify"],
    "Framer":[r"framerusercontent",r"framer\.com"]
}

SERVICE_TAXONOMY = {
    "Paid Media":["paid media","ppc","google ads","meta ads","facebook ads","linkedin ads","paid social","performance marketing","search ads","media buying"],
    "SEO":["seo","search engine optimization","organic search","technical seo","local seo","link building"],
    "AEO / AI Visibility":["aeo","answer engine optimization","generative engine optimization","geo","ai visibility","llm visibility","ai search"],
    "Social Media":["social media","community management","social strategy","content social","instagram","tiktok"],
    "Content Marketing":["content marketing","copywriting","editorial","content strategy","blog content","thought leadership"],
    "Branding":["branding","brand strategy","visual identity","brand identity","rebranding"],
    "Web / CRO":["web design","website development","web development","landing page","conversion rate optimization","cro","ux","ui/ux"],
    "Email / CRM":["email marketing","marketing automation","crm","lifecycle marketing","hubspot","klaviyo"],
    "Creative / Video":["creative","video production","motion","graphic design","ugc","ad creative"],
    "Analytics":["analytics","measurement","attribution","dashboard","business intelligence","marketing analytics"],
    "Lead Generation":["lead generation","demand generation","appointment setting","outbound","pipeline generation"],
    "Influencer Marketing":["influencer","creator marketing","influencer marketing"],
    "PR / Communications":["public relations","communications","media relations","pr"],
    "E-commerce":["ecommerce","e-commerce","shopify","marketplace","amazon"]
}

INDUSTRY_TAXONOMY = {
    "SaaS / Technology":["saas","software","technology","tech companies","b2b tech"],
    "E-commerce / Retail":["ecommerce","e-commerce","retail","shopify","consumer brands","dtc"],
    "Healthcare":["healthcare","health care","medical","dental","clinic","pharma"],
    "Education":["education","university","higher education","edtech","school"],
    "Finance / Fintech":["fintech","financial services","finance","banking","insurance"],
    "Real Estate":["real estate","property","realtor"],
    "Professional Services":["professional services","consulting","law firm","legal","accounting"],
    "Hospitality / Travel":["hospitality","hotel","travel","tourism","restaurant"],
    "Manufacturing / Industrial":["manufacturing","industrial","engineering"],
    "Local / SMB":["local businesses","small business","smb","small and medium"],
    "Enterprise":["enterprise","fortune 500","large companies"]
}

BUYER_ROLES = {
    "Founders / CEOs":["founder","ceo","business owner","entrepreneur"],
    "Marketing Leadership":["cmo","vp marketing","head of marketing","marketing director","marketing leader"],
    "Growth / Demand Gen":["growth lead","head of growth","demand generation","demand gen"],
    "Sales / Revenue":["cro","vp sales","sales leader","revenue leader"],
    "E-commerce Leadership":["ecommerce manager","e-commerce manager","head of ecommerce","digital commerce"],
    "Brand / Communications":["brand manager","communications director","head of brand"]
}

OFFER_SIGNALS = {
    "Free consultation":["free consultation","free strategy call","free discovery","book a free call"],
    "Free audit":["free audit","free assessment","free analysis","complimentary audit"],
    "Demo / discovery":["book a demo","book a call","discovery call","schedule a call","talk to us","talk to an expert"],
    "Productized package":["package","packages","starter plan","growth plan","pro plan"],
    "Retainer":["monthly retainer","retainer"],
    "Project-based":["project-based","fixed project","one-time project"],
    "Performance-based":["performance-based","pay per result","pay for performance","revenue share"],
    "Guarantee / risk reversal":["guarantee","money back","no long-term contract","cancel anytime","risk-free"],
    "Free tool / calculator":["free tool","calculator","grader","scorecard","generator"],
    "Lead magnet":["download guide","download report","ebook","whitepaper","template","checklist"]
}


BUSINESS_MODEL_SIGNALS = {
    "Retainer / mensualidad":["monthly retainer","retainer","monthly fee","monthly engagement"],
    "Proyecto":["project-based","fixed project","one-time project","per project"],
    "Performance / resultados":["performance-based","pay per result","pay for performance","revenue share","success fee"],
    "Paquetizado":["package","packages","starter plan","growth plan","pro plan","fixed package"],
    "Suscripción / recurrente":["subscription","monthly plan","recurring","membership"],
    "Cotización personalizada":["custom quote","custom proposal","tailored proposal","contact us for pricing","pricing upon request"]
}

GROWTH_SIGNAL_TERMS = {
    "Contratación activa":["we're hiring","we are hiring","join our team","open positions","careers"],
    "Expansión / nuevas oficinas":["new office","expanded to","expanding into","global offices","locations"],
    "Crecimiento declarado":["fast-growing","growing team","growth rate","inc 5000","deloitte fast"],
    "Reconocimientos":["award-winning","awards","top agency","agency of the year"],
    "Partners / certificaciones":["google partner","meta business partner","hubspot partner","shopify partner","certified partner"]
}

CONTENT_CATEGORIES = {
    "Blog / Insights":["/blog","/insights","/articles","/resources"],
    "Case Studies":["case-study","case-studies","success-stories","customers"],
    "Guides / Research":["guide","research","report","whitepaper","ebook"],
    "Webinars / Events":["webinar","event"],
    "Tools / Calculators":["tool","calculator","grader","assessment"]
}

def normalize_url(x):
    x=(x or "").strip()
    if not x:return ""
    if not re.match(r"^https?://",x,re.I):x="https://"+x
    return x.rstrip("/")

def fetch(url,timeout=18):
    t=time.perf_counter()
    try:
        r=requests.get(url,headers=HEADERS,timeout=timeout,allow_redirects=True)
        return {"ok":r.ok,"status":r.status_code,"url":r.url,"text":r.text if r.ok else "",
                "elapsed_ms":round((time.perf_counter()-t)*1000)}
    except Exception as e:
        return {"ok":False,"status":None,"url":url,"text":"","error":str(e),
                "elapsed_ms":round((time.perf_counter()-t)*1000)}

def search_web(query,max_results=8):
    try:
        from ddgs import DDGS
    except Exception:
        try:
            from duckduckgo_search import DDGS
        except Exception:
            return []
    out=[]
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query,max_results=max_results):
                out.append({"title":r.get("title",""),"url":r.get("href") or r.get("url",""),
                            "snippet":r.get("body") or r.get("snippet","")})
    except Exception:
        pass
    return out

def clean_text(html):
    soup=BeautifulSoup(html or "","html.parser")
    for t in soup(["script","style","noscript","svg"]):t.decompose()
    return re.sub(r"\s+"," ",soup.get_text(" ",strip=True)).strip()

def iter_jsonld(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values(): yield from iter_jsonld(v)
    elif isinstance(obj,list):
        for v in obj:yield from iter_jsonld(v)

def address_text(a):
    if isinstance(a,str):return a.strip()
    if not isinstance(a,dict):return None
    vals=[a.get("streetAddress"),a.get("addressLocality"),a.get("addressRegion"),a.get("postalCode"),a.get("addressCountry")]
    return ", ".join(str(v).strip() for v in vals if v)

def get_meta(soup,prop=None,name=None):
    attrs={"property":prop} if prop else {"name":name}
    t=soup.find("meta",attrs=attrs)
    return t.get("content","").strip() if t and t.get("content") else None

def company_profile(html,url):
    soup=BeautifulSoup(html or "","html.parser")
    p={"domain":urlparse(url).netloc.replace("www.",""),"website":url}
    orgs=[]
    schema_types=[]
    for tag in soup.find_all("script",type=lambda x:x and "ld+json" in x):
        try:
            data=json.loads(tag.string or tag.get_text() or "")
            for node in iter_jsonld(data):
                typ=node.get("@type")
                types=typ if isinstance(typ,list) else [typ]
                schema_types.extend([str(x) for x in types if x])
                if any(t in ["Organization","Corporation","LocalBusiness","ProfessionalService"] for t in types if t):
                    orgs.append(node)
        except Exception:pass
    org=orgs[0] if orgs else {}
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    p["name"]=org.get("name") or get_meta(soup,prop="og:site_name") or re.split(r"\s+[|\-–—]\s+",title)[0].strip() or p["domain"].split(".")[0].title()
    p["legal_name"]=org.get("legalName")
    p["description"]=org.get("description") or get_meta(soup,name="description") or get_meta(soup,prop="og:description")
    p["location"]=address_text(org.get("address"))
    p["email"]=org.get("email")
    p["phone"]=org.get("telephone")
    p["founded"]=org.get("foundingDate")
    same=org.get("sameAs") or []
    if isinstance(same,str):same=[same]
    p["same_as"]=same
    p["schema_types"]=sorted(set(schema_types))
    p["title"]=title
    p["meta_description"]=get_meta(soup,name="description")
    p["canonical"]=(soup.find("link",rel="canonical") or {}).get("href") if soup.find("link",rel="canonical") else None
    p["viewport"]=bool(soup.find("meta",attrs={"name":"viewport"}))
    p["h1"]=[re.sub(r"\s+"," ",x.get_text(" ",strip=True)) for x in soup.find_all("h1")][:5]
    return p

def first_party_socials(html,base,same_as):
    soup=BeautifulSoup(html or "","html.parser")
    urls=list(same_as or [])+[urljoin(base,a["href"]) for a in soup.find_all("a",href=True)]
    found={}
    for u in urls:
        low=u.lower()
        for platform,needles in SOCIAL_DOMAINS.items():
            if any(n in low for n in needles) and "share" not in low and "/intent/" not in low:
                found.setdefault(platform,{"url":u.split("?")[0].rstrip("/"),"evidence":"first-party"})
    return found

def verify_social(name,domain,platform):
    sites={"LinkedIn":"linkedin.com/company","Instagram":"instagram.com","Facebook":"facebook.com",
           "YouTube":"youtube.com","TikTok":"tiktok.com","X":"x.com"}
    for q in [f'"{domain}" site:{sites[platform]}',f'"{name}" "{domain}" site:{sites[platform]}']:
        for r in search_web(q,5):
            blob=(r["title"]+" "+r["snippet"]).lower()
            if any(n in r["url"].lower() for n in SOCIAL_DOMAINS[platform]) and (domain.lower() in blob or name.lower() in blob):
                return {"url":r["url"].split("?")[0],"evidence":"domain-validated-search"}
    return None

def social_profiles(p,html,url):
    found=first_party_socials(html,url,p.get("same_as"))
    for platform in SOCIAL_DOMAINS:
        if platform not in found:
            cand=verify_social(p["name"],p["domain"],platform)
            if cand:found[platform]=cand
    return found

def internal_links(html,base):
    soup=BeautifulSoup(html or "","html.parser")
    out=[]
    host=urlparse(base).netloc
    seen=set()
    for a in soup.find_all("a",href=True):
        u=urljoin(base,a["href"].split("#")[0])
        if urlparse(u).netloc==host and u not in seen:
            seen.add(u);out.append({"url":u,"text":re.sub(r"\s+"," ",a.get_text(" ",strip=True))[:120]})
    return out

def key_pages(links):
    out={}
    groups={
        "about":["about","company","who-we-are"],
        "services":["services","solutions","capabilities"],
        "pricing":["pricing","plans","packages"],
        "case_studies":["case-study","case-studies","success-stories","customers","work"],
        "resources":["blog","resources","insights","articles"],
        "contact":["contact","book","demo","discovery"],
        "team":["team","leadership","people"],
        "careers":["careers","jobs","join-us"]
    }
    for item in links:
        low=(item["text"]+" "+item["url"]).lower()
        for k,words in groups.items():
            if k not in out and any(w in low for w in words):out[k]=item["url"]
    return out

def fetch_sitemap(base):
    urls=[]
    candidates=[urljoin(base,"/sitemap.xml"),urljoin(base,"/sitemap_index.xml")]
    for sm in candidates:
        r=fetch(sm,12)
        if not r["ok"]:continue
        try:
            root=ET.fromstring(r["text"])
            locs=[e.text.strip() for e in root.iter() if e.tag.endswith("loc") and e.text]
            # Sitemap index: fetch a few child sitemaps.
            if any(x.endswith(".xml") for x in locs[:5]):
                child_urls=[]
                for child in locs[:6]:
                    cr=fetch(child,12)
                    if cr["ok"]:
                        try:
                            rr=ET.fromstring(cr["text"])
                            child_urls += [e.text.strip() for e in rr.iter() if e.tag.endswith("loc") and e.text]
                        except Exception:pass
                locs=child_urls
            urls=locs[:300]
            if urls:break
        except Exception:continue
    return urls

def categorize_urls(urls):
    counts={k:0 for k in CONTENT_CATEGORIES}
    for u in urls:
        low=u.lower()
        for k,words in CONTENT_CATEGORIES.items():
            if any(w in low for w in words):counts[k]+=1
    return counts

def detect_technologies(html):
    return [{"technology":k,"detected":any(re.search(p,html or "",re.I) for p in ps)}
            for k,ps in TECH_PATTERNS.items()]

def detect_taxonomy(text,taxonomy):
    low=text.lower()
    out=[]
    for label,terms in taxonomy.items():
        hits=[t for t in terms if t in low]
        if hits:out.append({"label":label,"evidence":hits[:6],"hits":sum(low.count(t) for t in terms)})
    return sorted(out,key=lambda x:x["hits"],reverse=True)

def offer_signals(text):
    low=text.lower()
    out=[]
    for label,terms in OFFER_SIGNALS.items():
        hits=[t for t in terms if t in low]
        if hits:out.append({"label":label,"evidence":hits[:4]})
    return out

def extract_prices(text):
    pats=[
        r"(?:\$|USD\s*)[\d,.]+(?:\s*(?:/mo|per month|monthly|/month))?",
        r"(?:COP|€|£)\s*[\d,.]+(?:\s*(?:/mo|per month|monthly|/month))?"
    ]
    out=[]
    for pat in pats:
        for m in re.finditer(pat,text,re.I):
            v=m.group(0)
            if v not in out:out.append(v)
    return out[:15]

def quantified_proof(text):
    pats=[
        r"\$[\d,.]+\s*[kKmMbB]?\s+(?:in\s+)?(?:new\s+)?(?:pipeline|revenue|sales)",
        r"\b\d{1,4}\+?\s+(?:qualified\s+)?(?:meetings|leads|opportunities|customers|clients)",
        r"\b\d{1,3}(?:\.\d+)?%\s+(?:increase|growth|lift|conversion|reduction|improvement|roi|roas)",
        r"\b\d+(?:\.\d+)?x\s+(?:roi|roas|growth|return|pipeline)"
    ]
    out=[]
    for pat in pats:
        for m in re.finditer(pat,text,re.I):
            v=m.group(0)
            if v.lower() not in [x.lower() for x in out]:out.append(v)
    return out[:20]

def extract_ctas(html,base):
    soup=BeautifulSoup(html or "","html.parser")
    words=["book","demo","contact","get started","talk","quote","audit","consult","strategy","download","pricing","schedule","apply"]
    out=[];seen=set()
    for a in soup.find_all("a",href=True):
        label=re.sub(r"\s+"," ",a.get_text(" ",strip=True)).strip()
        if label and any(w in label.lower() for w in words):
            u=urljoin(base,a["href"]);key=(label.lower(),u)
            if key not in seen:seen.add(key);out.append({"label":label[:120],"url":u})
    return out[:20]

def forms_analysis(html):
    soup=BeautifulSoup(html or "","html.parser")
    forms=[]
    for f in soup.find_all("form"):
        fields=[]
        for inp in f.find_all(["input","textarea","select"]):
            typ=(inp.get("type") or inp.name or "").lower()
            if typ in ["hidden","submit","button"]:continue
            fields.append(inp.get("name") or inp.get("placeholder") or typ)
        forms.append({"fields":len(fields),"field_names":fields[:15]})
    return {"count":len(forms),"forms":forms[:10],
            "avg_fields":round(sum(x["fields"] for x in forms)/len(forms),1) if forms else 0}

def seo_audit(p,html,sitemap_urls,base):
    soup=BeautifulSoup(html,"html.parser")
    robots=fetch(urljoin(base,"/robots.txt"),10)
    llms=fetch(urljoin(base,"/llms.txt"),10)
    faq_schema="FAQPage" in p.get("schema_types",[])
    org_schema=any(x in p.get("schema_types",[]) for x in ["Organization","Corporation","LocalBusiness","ProfessionalService"])
    score=0
    checks={
        "HTTPS":base.startswith("https://"),
        "Title":bool(p.get("title")),
        "Meta description":bool(p.get("meta_description")),
        "H1":bool(p.get("h1")),
        "Canonical":bool(p.get("canonical")),
        "Viewport":bool(p.get("viewport")),
        "Robots.txt":robots["ok"],
        "Sitemap":bool(sitemap_urls),
        "Organization schema":org_schema,
        "FAQ schema":faq_schema,
        "llms.txt":llms["ok"]
    }
    for v in checks.values():
        if v:score+=1
    return {"score":round(100*score/len(checks)),"checks":checks}


def detect_business_models(text):
    low=text.lower()
    out=[]
    for label,terms in BUSINESS_MODEL_SIGNALS.items():
        hits=[t for t in terms if t in low]
        if hits:
            out.append({"label":label,"evidence":hits[:5]})
    return out

def detect_growth_signals(text,key_pages):
    low=text.lower()
    out=[]
    for label,terms in GROWTH_SIGNAL_TERMS.items():
        hits=[t for t in terms if t in low]
        if hits:
            out.append({"label":label,"evidence":hits[:5],"source":"copy"})
    if key_pages.get("careers") and not any(x["label"]=="Contratación activa" for x in out):
        out.append({"label":"Contratación activa","evidence":["careers page"],"source":"site structure"})
    if key_pages.get("team"):
        out.append({"label":"Equipo visible","evidence":["team / leadership page"],"source":"site structure"})
    return out

def acquisition_mix(data):
    channels=[]
    content_total=sum(data["content_footprint"].values())
    detected_tech={x["technology"] for x in data["technology_stack"] if x["detected"]}
    offers={x["label"] for x in data["offers"]}

    if content_total>=3 or data["seo"]["score"]>=65:
        channels.append({"channel":"SEO / contenido","evidence":f"{content_total} activos de contenido + SEO/AEO {data['seo']['score']}/100"})
    paid=[x for x in ["Google Ads","Meta Pixel","LinkedIn Insight","TikTok Pixel"] if x in detected_tech]
    if paid:
        channels.append({"channel":"Paid media","evidence":", ".join(paid)})
    if data["socials"]:
        channels.append({"channel":"Social orgánico","evidence":", ".join(data["socials"].keys())})
    if data["clutch"]:
        channels.append({"channel":"Reputación / reviews","evidence":"Señal indexada en Clutch"})
    if "Lead magnet" in offers or "Free tool / calculator" in offers:
        channels.append({"channel":"Captura inbound","evidence":"Lead magnet o herramienta gratuita"})
    if "Demo / discovery" in offers or data["key_pages"].get("contact"):
        channels.append({"channel":"Venta consultiva / directa","evidence":"Demo, discovery o contacto comercial"})
    if any(x["label"]=="Lead Generation" for x in data["services"]):
        channels.append({"channel":"Prospección / demanda","evidence":"Oferta pública de lead/demand generation"})
    return channels

def sales_motion(data):
    labels={x["label"] for x in data["offers"]}
    motions=[]
    if "Productized package" in labels or "Paquetizado" in {x["label"] for x in data.get("business_models",[])}:
        motions.append("Paquetizado / estandarizado")
    if "Demo / discovery" in labels or data["key_pages"].get("contact"):
        motions.append("Venta consultiva")
    if "Free audit" in labels:
        motions.append("Audit-led")
    if "Performance-based" in labels or "Performance / resultados" in {x["label"] for x in data.get("business_models",[])}:
        motions.append("Performance-led")
    if "Lead magnet" in labels or "Free tool / calculator" in labels:
        motions.append("Inbound / educación")
    if data["prices"] and ("Productized package" in labels or "Paquetizado" in {x["label"] for x in data.get("business_models",[])}):
        motions.append("Baja fricción / pricing visible")
    return list(dict.fromkeys(motions)) or ["No concluyente"]

def maturity_proxy(data):
    points=0
    reasons=[]
    content=sum(data["content_footprint"].values())
    cases=data["content_footprint"].get("Case Studies",0)
    tech=sum(1 for x in data["technology_stack"] if x["detected"])

    if data["profile"].get("founded"):
        points+=8; reasons.append("Fecha de fundación pública")
    if data["key_pages"].get("team"):
        points+=8; reasons.append("Equipo/liderazgo visible")
    if data["key_pages"].get("careers"):
        points+=10; reasons.append("Página de empleo")
    if cases>=3:
        points+=15; reasons.append("Biblioteca de casos")
    elif cases>0:
        points+=7; reasons.append("Casos de éxito")
    if len(data["proof_points"])>=3:
        points+=15; reasons.append("Prueba cuantificada")
    elif data["proof_points"]:
        points+=7; reasons.append("Claims cuantificados")
    if content>=15:
        points+=12; reasons.append("Motor de contenido")
    elif content>=3:
        points+=6; reasons.append("Contenido activo")
    if tech>=5:
        points+=12; reasons.append("Stack MarTech amplio")
    elif tech>=2:
        points+=6; reasons.append("Stack MarTech visible")
    if len(data["socials"])>=4:
        points+=8; reasons.append("Presencia multicanal")
    elif len(data["socials"])>=2:
        points+=4; reasons.append("Presencia social")
    if data["clutch"]:
        points+=7; reasons.append("Prueba/reviews de terceros")
    if data["prices"]:
        points+=5; reasons.append("Pricing visible")

    score=min(100,points)
    if score>=75: label="Madurez pública alta"
    elif score>=50: label="Madurez pública media-alta"
    elif score>=30: label="Madurez pública media"
    else: label="Madurez pública temprana / baja evidencia"
    return {"score":score,"label":label,"reasons":reasons}

def commercial_transparency(data):
    score=0
    signals=[]
    if data["prices"]:
        score+=25; signals.append("Precios visibles")
    if data["business_models"]:
        score+=20; signals.append("Modelo comercial identificable")
    if data["key_pages"].get("case_studies"):
        score+=15; signals.append("Casos de éxito")
    if data["proof_points"]:
        score+=15; signals.append("Resultados cuantificados")
    if data["ctas"]:
        score+=10; signals.append("CTA comercial claro")
    if data["profile"].get("location"):
        score+=5; signals.append("Ubicación pública")
    if data["key_pages"].get("team"):
        score+=5; signals.append("Equipo visible")
    if data["clutch"]:
        score+=5; signals.append("Reviews de terceros")
    return {"score":min(100,score),"signals":signals}

def managerial_risks(data):
    risks=[]
    if len(data["services"])>=9 and len(data["industries"])>=5:
        risks.append({"risk":"Posicionamiento potencialmente generalista","why":"Muchos servicios y muchos sectores aparecen simultáneamente."})
    if not data["proof_points"] and not data["key_pages"].get("case_studies"):
        risks.append({"risk":"Brecha de prueba pública","why":"No se detectaron resultados cuantificados ni una página clara de casos."})
    if not data["prices"] and not data["business_models"]:
        risks.append({"risk":"Modelo comercial poco visible","why":"Desde fuera no es fácil entender cómo cobra o estructura su servicio."})
    if data["forms"]["avg_fields"] and data["forms"]["avg_fields"]>=7:
        risks.append({"risk":"Posible fricción de conversión","why":f"El formulario principal promedia {data['forms']['avg_fields']} campos."})
    if len(data.get("acquisition_mix",[]))<=2:
        risks.append({"risk":"Adquisición visible poco diversificada","why":"Se detectaron dos o menos mecanismos públicos de adquisición."})
    if data["seo"]["score"]<50:
        risks.append({"risk":"Higiene SEO/AEO mejorable","why":f"Score técnico visible de {data['seo']['score']}/100."})
    return risks

def financial_lens(data):
    recurring=any(x["label"] in ["Retainer / mensualidad","Suscripción / recurrente"] for x in data["business_models"])
    performance=any(x["label"]=="Performance / resultados" for x in data["business_models"])
    pricing=bool(data["prices"])
    return {
        "Ingresos":{
            "visibility":"Proxy observable",
            "detail":"No se observa revenue total. Se usan pricing, modelo comercial, casos y claims como señales de monetización."
        },
        "Costos":{
            "visibility":"No público",
            "detail":"La estructura de costos de una agencia privada no puede deducirse de forma confiable desde su web."
        },
        "EBITDA":{
            "visibility":"No público",
            "detail":"No se calcula EBITDA del competidor sin estados financieros o disclosures verificables."
        },
        "Deuda":{
            "visibility":"No público",
            "detail":"No se infiere endeudamiento a partir de señales de marketing."
        },
        "ROE":{
            "visibility":"No público",
            "detail":"No se calcula retorno sobre patrimonio sin utilidad neta y patrimonio verificables."
        },
        "Modelo de ingreso":{
            "visibility":"Inferencia pública",
            "detail":("Recurrente" if recurring else "No recurrente/no concluyente") +
                     (" + performance" if performance else "") +
                     (" + pricing público" if pricing else "")
        }
    }

def build_business_intelligence(data,corpus):
    data["business_models"]=detect_business_models(corpus)
    data["growth_signals"]=detect_growth_signals(corpus,data["key_pages"])
    data["acquisition_mix"]=acquisition_mix(data)
    data["sales_motion"]=sales_motion(data)
    data["maturity_proxy"]=maturity_proxy(data)
    data["commercial_transparency"]=commercial_transparency(data)
    data["managerial_risks"]=managerial_risks(data)
    data["financial_lens"]=financial_lens(data)
    return data

def score_model(data):
    # Internal heuristic benchmark, not an industry standard.
    service_count=len(data["services"])
    industry_count=len(data["industries"])
    offers={x["label"] for x in data["offers"]}
    proof=len(data["proof_points"])
    content=sum(data["content_footprint"].values())
    ctas=len(data["ctas"])
    socials=len(data["socials"])
    tech=sum(1 for x in data["technology_stack"] if x["detected"])
    pricing=bool(data["prices"])
    case_count=data["content_footprint"].get("Case Studies",0)

    positioning=min(100,25+service_count*5+industry_count*8+(15 if data["profile"].get("h1") else 0))
    offer=min(100,20+len(offers)*9+(15 if pricing else 0)+(10 if "Guarantee / risk reversal" in offers else 0))
    proof_score=min(100,proof*12+case_count*5+(10 if data["key_pages"].get("case_studies") else 0))
    funnel=min(100,ctas*5+(15 if data["forms"]["count"] else 0)+(15 if any(x["technology"] in ["Calendly","Chili Piper","HubSpot"] and x["detected"] for x in data["technology_stack"]) else 0))
    content_score=min(100,10+min(content,70))
    paid=min(100,sum(20 for x in data["technology_stack"] if x["technology"] in ["Google Ads","Meta Pixel","LinkedIn Insight","TikTok Pixel"] and x["detected"]))
    presence=min(100,socials*14)
    seo=data["seo"]["score"]
    return {"Positioning":round(positioning),"Offer":round(offer),"Proof":round(proof_score),
            "Funnel":round(funnel),"Content":round(content_score),"Paid readiness":round(paid),
            "Social presence":round(presence),"SEO/AEO hygiene":round(seo)}

def ad_links(name,country):
    return {
        "Meta Ad Library":f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country={quote_plus(country)}&q={quote_plus(name)}&search_type=keyword_unordered",
        "Google Ads Transparency":"https://adstransparency.google.com/?region="+quote_plus(country),
        "LinkedIn Ad Library":"https://www.linkedin.com/ad-library/home",
        "TikTok Creative Center":"https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"
    }

def clutch_signal(name):
    results=search_web(f'site:clutch.co "{name}"',5)
    out=[]
    for r in results:
        if "clutch.co" in r["url"]:
            blob=(r["title"]+" "+r["snippet"])
            rating=None;reviews=None
            m=re.search(r"([1-5](?:\.\d)?)\s*(?:/5|stars?)",blob,re.I)
            if m:rating=m.group(1)
            m2=re.search(r"(\d+)\s+reviews?",blob,re.I)
            if m2:reviews=m2.group(1)
            out.append({"title":r["title"],"url":r["url"],"rating":rating,"reviews":reviews})
    return out[:3]

def analyze_domain(domain,country="US"):
    home=fetch(normalize_url(domain))
    if not home["ok"]:
        return {"ok":False,"domain":domain,"error":f"Could not fetch website: {home.get('error') or home.get('status')}"}
    p=company_profile(home["text"],home["url"])
    links=internal_links(home["text"],home["url"])
    kp=key_pages(links);p["key_pages"]=kp
    # Crawl a bounded set of strategically useful pages.
    page_urls=[home["url"]]+list(dict.fromkeys(kp.values()))[:8]
    texts=[];htmls=[]
    for u in page_urls:
        r=home if u==home["url"] else fetch(u,14)
        if r["ok"]:
            texts.append(clean_text(r["text"]))
            htmls.append((u,r["text"]))
    corpus=" ".join(texts)
    # Fill missing location from About/Contact copy.
    if not p.get("location"):
        for pat in [r"(?:headquarters|headquartered|based)\s+(?:in|at)\s+([A-Z][A-Za-z .'-]+,\s*[A-Z][A-Za-z .'-]+)",
                    r"(?:located in|location[:\s]+)\s*([A-Z][A-Za-z .'-]+,\s*[A-Z][A-Za-z .'-]+)"]:
            m=re.search(pat,corpus)
            if m:p["location"]=m.group(1).strip();break
    sm=fetch_sitemap(home["url"])
    content_counts=categorize_urls(sm)
    socials=social_profiles(p,home["text"],home["url"])
    services=detect_taxonomy(corpus,SERVICE_TAXONOMY)
    industries=detect_taxonomy(corpus,INDUSTRY_TAXONOMY)
    roles=detect_taxonomy(corpus,BUYER_ROLES)
    offers=offer_signals(corpus)
    prices=extract_prices(corpus)
    proof=quantified_proof(corpus)
    ctas=extract_ctas(home["text"],home["url"])
    forms=forms_analysis(home["text"])
    tech=detect_technologies(home["text"])
    seo=seo_audit(p,home["text"],sm,home["url"])
    data={
        "ok":True,"profile":p,"key_pages":kp,"services":services,"industries":industries,
        "buyer_roles":roles,"offers":offers,"prices":prices,"proof_points":proof,
        "ctas":ctas,"forms":forms,"socials":socials,"technology_stack":tech,
        "content_footprint":content_counts,"sitemap_pages":len(sm),
        "seo":seo,"response_ms":home["elapsed_ms"],"homepage_bytes":len(home["text"].encode("utf-8")),
        "ad_library_links":ad_links(p["name"],country),
        "clutch":clutch_signal(p["name"]),
        "evidence_notes":[
            "All website claims are derived from public pages discovered from the domain.",
            "Services, industries and buyer roles are taxonomy-based classifications of public copy, not private company data.",
            "Ad pixels indicate advertising infrastructure, not proof that a campaign is currently active.",
            "Ad Library links are provided for verification; exact spend/targeting is only public in limited transparency contexts.",
            "Benchmark scores are internal heuristics designed for comparison, not industry-standard ratings."
        ]
    }
    data=build_business_intelligence(data,corpus)
    data["scores"]=score_model(data)
    return data

def comparison(results):
    good=[r for r in results if r.get("ok")]
    rows=[]
    service_freq=Counter();industry_freq=Counter();offer_freq=Counter()
    for r in good:
        for x in r["services"]:service_freq[x["label"]]+=1
        for x in r["industries"]:industry_freq[x["label"]]+=1
        for x in r["offers"]:offer_freq[x["label"]]+=1
        s=r["scores"];p=r["profile"]
        rows.append({
            "name":p["name"],"domain":p["domain"],"location":p.get("location"),
            "services":len(r["services"]),"industries":len(r["industries"]),
            "pricing_public":bool(r["prices"]),"proof_points":len(r["proof_points"]),
            "case_studies":r["content_footprint"].get("Case Studies",0),
            "content_pages":sum(r["content_footprint"].values()),
            "social_networks":len(r["socials"]),"ad_pixels":sum(1 for x in r["technology_stack"] if x["technology"] in ["Google Ads","Meta Pixel","LinkedIn Insight","TikTok Pixel"] and x["detected"]),
            "seo_score":r["seo"]["score"],"response_ms":r["response_ms"],
            "positioning_score":s["Positioning"],"offer_score":s["Offer"],"proof_score":s["Proof"],
            "funnel_score":s["Funnel"],"content_score":s["Content"],"paid_score":s["Paid readiness"],
            "maturity_score":r["maturity_proxy"]["score"],
            "maturity_label":r["maturity_proxy"]["label"],
            "commercial_transparency":r["commercial_transparency"]["score"],
            "acquisition_channels":len(r["acquisition_mix"]),
            "business_models":", ".join(x["label"] for x in r["business_models"]),
            "growth_signals":len(r["growth_signals"]),
            "managerial_risks":len(r["managerial_risks"])
        })
    n=len(good) or 1
    def freq_rows(counter):
        return [{"label":k,"count":v,"share_pct":round(100*v/n,1)} for k,v in counter.most_common()]
    # Whitespace = present in taxonomy but used by few competitors; only include things observed at least once.
    white_services=[x for x in freq_rows(service_freq) if x["share_pct"]<=40]
    saturated_services=[x for x in freq_rows(service_freq) if x["share_pct"]>=70]
    white_industries=[x for x in freq_rows(industry_freq) if x["share_pct"]<=40]
    executive=[]
    if rows:
        def leader(key):
            return max(rows,key=lambda x:x.get(key,0))
        executive.append({"title":"Mayor claridad de posicionamiento","company":leader("positioning_score")["name"],"value":leader("positioning_score")["positioning_score"]})
        executive.append({"title":"Prueba comercial más fuerte","company":leader("proof_score")["name"],"value":leader("proof_score")["proof_score"]})
        executive.append({"title":"Mayor madurez pública","company":leader("maturity_score")["name"],"value":leader("maturity_score")["maturity_score"]})
        executive.append({"title":"Mayor transparencia comercial","company":leader("commercial_transparency")["name"],"value":leader("commercial_transparency")["commercial_transparency"]})
        executive.append({"title":"Mix de adquisición más amplio","company":leader("acquisition_channels")["name"],"value":leader("acquisition_channels")["acquisition_channels"]})

    pricing_count=sum(1 for x in rows if x["pricing_public"])
    strategic=[]
    if rows and pricing_count/len(rows)<=0.4:
        strategic.append("La mayoría de las agencias no publica precios: una oferta paquetizada o con rangos visibles podría reducir fricción comercial.")
    if white_services:
        strategic.append("Hay servicios presentes en pocos competidores; conviene validar demanda antes de tratarlos como oportunidad real.")
    if saturated_services:
        strategic.append("Varias categorías están saturadas; competir solo por servicio puede ser débil sin nicho, prueba o modelo de oferta diferencial.")
    if rows and sum(1 for x in rows if x["proof_points"]==0)/len(rows)>=0.5:
        strategic.append("La prueba cuantificada es débil en buena parte del set: demostrar impacto en revenue, pipeline o eficiencia puede ser un diferenciador.")
    if rows and sum(1 for x in rows if x["acquisition_channels"]<=2)/len(rows)>=0.5:
        strategic.append("Muchos competidores muestran un mix de adquisición limitado; una estrategia multicanal bien instrumentada puede ser una ventaja.")

    return {
        "companies":rows,
        "service_frequency":freq_rows(service_freq),
        "industry_frequency":freq_rows(industry_freq),
        "offer_frequency":freq_rows(offer_freq),
        "whitespace":{"services":white_services,"industries":white_industries,
                      "saturated_services":saturated_services},
        "executive_insights":executive,
        "strategic_readout":strategic
    }

@app.route("/")
def index():return render_template("index.html")

@app.route("/api/compare",methods=["POST"])
def api_compare():
    j=request.get_json(force=True)
    domains=[x.strip() for x in j.get("domains",[]) if x.strip()][:8]
    country=j.get("country","US")
    results=[]
    with ThreadPoolExecutor(max_workers=min(4,len(domains) or 1)) as ex:
        futs={ex.submit(analyze_domain,d,country):d for d in domains}
        for f in as_completed(futs):
            try:results.append(f.result())
            except Exception as e:results.append({"ok":False,"domain":futs[f],"error":str(e)})
    order={urlparse(normalize_url(d)).netloc.replace("www.",""):i for i,d in enumerate(domains)}
    results.sort(key=lambda r:order.get((r.get("profile") or {}).get("domain",r.get("domain","")),999))
    return jsonify({"ok":True,"results":results,"comparison":comparison(results)})

@app.route("/health")
def health():return {"ok":True,"service":"AgencyScope V3"}

if __name__=="__main__":
    app.run(host="127.0.0.1",port=int(os.getenv("PORT","5000")),debug=True)
