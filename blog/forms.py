from django import forms
from .models import Comment


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25) # the name of the person sending the post
    email = forms.EmailField() # the email of the person sending the post recommendation.
    to = forms.EmailField() # the email of the recipient.
    comments = forms.CharField(required=False, widget=forms.Textarea) # for comments to include in post recommendation email.


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body']


class SearchForm(forms.Form):
    query = forms.CharField()
