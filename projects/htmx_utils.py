from django.http import HttpResponse

def htmx_redirect(url):
    response = HttpResponse()
    response['HX-Redirect'] = url
    return response

def htmx_push_url(response, url):
    response['HX-Push-Url'] = url
    return response
