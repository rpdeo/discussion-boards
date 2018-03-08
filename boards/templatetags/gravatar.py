import hashlib
from urllib.parse import urlencode
from django import template

register = template.Library()


@register.filter
def gravatar(user):
    email = user.email.lower().encode('utf-8')
    default = 'mm'
    size = 256
    url = 'https://www.gravatar.com/avatar/{md5}?{params}'.format(
        md5=hashlib.md5(email).hexdigest(),
        params=urlencode({'d': default, 's': str(size)})
    )
    return url

#
# how to use in templates
# first: {% load gravatar %}
# then where necessary: <img src="{{ post.created_by|gravatar }}" alt="{{ post.created_by.username }}" class="w-100 rounded">
#
