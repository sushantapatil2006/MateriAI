from django.db import models

class StudyMaterial(models.Model):
    summary = models.TextField()
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    material = models.ForeignKey(StudyMaterial, related_name='questions', on_delete=models.CASCADE)
    question_text = models.CharField(max_length=1000)
    options = models.JSONField() # List of 4 strings
    correct_answer = models.CharField(max_length=500)
    order = models.IntegerField(default=0)
