from django.conf.urls import patterns, include, url

urlpatterns = patterns('team.views',

    url(r'^importMetrics/', 'csvUpload'),
    url(r'^webApi/', 'webAPI'),
    url(r'^displayTeam/', 'displayTeam'),
    url(r'^updateGoogle/', 'updateGoogle'),

)