from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional


class RunbookForm(FlaskForm):
    """Runbook creation and edit form."""
    title = StringField("Runbook Title", validators=[
        DataRequired(message="Title is required"),
        Length(max=255, message="Title cannot exceed 255 characters")
    ])
    description = TextAreaField("Description", validators=[
        Optional(),
        Length(max=2000, message="Description cannot exceed 2000 characters")
    ])
    status = SelectField("Status", choices=[
        ("active", "Active"),
        ("inactive", "Inactive")
    ], default="active")
    steps_json = HiddenField("Steps JSON")
    submit = SubmitField("Save Runbook")


class VersionForm(FlaskForm):
    """Create a new version of an existing runbook."""
    version_note = StringField("Version / Change Log Note", validators=[
        Optional(),
        Length(max=255, message="Note cannot exceed 255 characters")
    ])
    submit = SubmitField("Create Version")
