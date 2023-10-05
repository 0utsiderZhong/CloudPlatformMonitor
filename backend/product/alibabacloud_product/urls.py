from . import views
from django.urls import path

app_name = "alibabacloud"

urlpatterns = [
    path('api/ecs/list', views.get_ecr_list),
    path('api/ecs/search', views.search_ecr),
    path('api/ecs/init', views.init_ecr_list),

    path('api/waf/init', views.init_waf_list),
    path('api/waf/list', views.get_waf_list),
    path('api/waf/search', views.search_waf),

    path('api/slb/init', views.init_slb_list),
    path('api/slb/list', views.get_slb_list),
    path('api/slb/search', views.search_slb),

    path('api/alb/init', views.init_alb_list),
    path('api/alb/list', views.get_alb_list),
    path('api/alb/search', views.search_alb),

    path('api/eip/init', views.init_eip_list),
    path('api/eip/list', views.get_eip_list),
    path('api/eip/search', views.search_eip),

    path('api/ssl/init', views.init_ssl_list),
    path('api/ssl/list', views.get_ssl_list),
    path('api/ssl/search', views.search_ssl),

    path('api/csc/init', views.init_csc_list),
    path('api/csc/list', views.get_csc_list),
]
