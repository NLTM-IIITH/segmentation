from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def meta(self):
        return self._meta
