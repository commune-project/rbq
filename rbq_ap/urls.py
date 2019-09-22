"""rbq URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter
#from rbq_cs.controllers.mastodon_api.account_viewset import AccountViewSet
#from rbq_cs.controllers.mastodon_api.status_viewset import StatusViewSet

from rbq_ap import views

# Create a router and register our viewsets with it.
router = DefaultRouter(trailing_slash=False)
router.register(r'users', views.ActorViewSet)
#router.register(r'statuses', StatusViewSet)

urlpatterns = router.urls + [
    # debug
    path(".well-known/webfinger", views.webfinger),
    path('admin/', admin.site.urls),

    path('inbox', views.inbox_view),
    path('<path:path>', views.find_object_or_activity),
]
