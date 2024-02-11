from django.forms import ModelForm
from. models import *
from django import forms


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = [
            'r_number',
            'numb_cabins_per_room'
        ]


class InstructorForm(ModelForm):
    class Meta:
        model = Instructor
        fields = [
            'did',
            'name'
        ]


class MeetingTimeForm(ModelForm):
    class Meta:
        model = MeetingTime
        fields = [
            'pid',
            'time',
            'day'
        ]
        widgets = {
            'pid': forms.TextInput(),
            'time': forms.Select(),
            'day': forms.Select(),
        }


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ['patient_number', 'patient_name', 'doctors']


class DepartmentForm(ModelForm):
    class Meta:
        model = Department
        fields = ['spec_name', 'patients']


class SectionForm(ModelForm):
    class Meta:
        model = Section
        fields = ['section_id', 'specialization', 'num_appointments_in_week']
