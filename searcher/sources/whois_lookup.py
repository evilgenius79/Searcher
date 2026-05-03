import whois


def lookup_domain(domain: str) -> dict:
    try:
        w = whois.whois(domain)
        result = {}
        for field in [
            "registrar",
            "creation_date",
            "expiration_date",
            "name_servers",
            "org",
            "country",
            "emails",
            "status",
        ]:
            val = getattr(w, field, None)
            if val and str(val) not in ("None", "[]", "{}"):
                result[field] = str(val)
        return result
    except Exception:
        return {}
