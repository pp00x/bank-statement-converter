from django.db import models
from django.utils import timezone

# Create your models here.


class StatementData(models.Model):
    pdf_filename = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    extracted_data = models.JSONField()  # Stores the list of transaction dicts

    def __str__(self):
        filename = self.pdf_filename or "Unknown file"
        return f"Statement from {filename} uploaded at {self.uploaded_at}"

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = "Statement Data Records"  # Optional: Nicer name in admin
