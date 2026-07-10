from django.db import models

class SearchHistory(models.Model):
    query = models.CharField(max_length=200)
    searched_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-searched_at']
    def __str__(self):
        return self.query
