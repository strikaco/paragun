from django.conf import settings
import ldap

LDAP = getattr(settings, 'LDAP', None)

def ldap_query(key, value):
    """
    Queries predefined LDAP connector for the given k:v pair.
    
    Args:
        key (str): Key to query LDAP for (uid, mail, etc.).
        value (str): Value to query LDAP for.
        
    Returns:
        data (dict): Dict of values containing LDAP response.
    """
    if not LDAP: return {}
    
    data = {}
    base = settings.LDAP_BASE
    query = '(%(key)s=%(value)s)' % {
        'key': key,
        'value': value.strip()
    }
    
    result = LDAP.search_s(base, ldap.SCOPE_SUBTREE, query)
    if result: qs, data = result
    return data