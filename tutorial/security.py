USERS = {
    'manager': 'manager',
    'editor': 'editor',
    'viewer': 'viewer'}

GROUPS = {
    'editor': ['group:editors'],
    'manager': ['group:editors']}


def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])
