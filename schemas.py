"""Pydantic models for the Resume schema, with strict validation."""
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

MONTH_RE = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PLACEHOLDERS = {"unknown", "n/a", "na", "none", "null", "not provided", "not specified"}


class Education(BaseModel):
    degree: str = Field(description="Degree or qualification, e.g. B.Tech in Computer Science")
    institution: str
    start_year: Optional[int] = Field(default=None, ge=1950, le=2100)
    end_year: Optional[int] = Field(default=None, ge=1950, le=2100)
    grade: Optional[str] = Field(default=None, description="CGPA, percentage, etc. as written")

    @model_validator(mode="after")
    def check_years(self):
        if self.start_year and self.end_year and self.end_year < self.start_year:
            raise ValueError("education end_year is before start_year")
        return self


class Experience(BaseModel):
    title: str
    company: str
    start_date: Optional[str] = Field(default=None, description="YYYY-MM, or just YYYY if no month is given")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM, or just YYYY if no month is given; null if current")
    is_current: bool = False
    highlights: list[str] = Field(default_factory=list)

    @field_validator("start_date", "end_date")
    @classmethod
    def check_month_format(cls, v):
        if v is not None and not MONTH_RE.match(v):
            raise ValueError(f"date '{v}' must be in YYYY-MM or YYYY format")
        return v

    @model_validator(mode="after")
    def check_dates(self):
        if self.is_current and self.end_date is not None:
            raise ValueError("is_current is true but end_date is set")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("experience end_date is before start_date")
        return self


class Resume(BaseModel):
    full_name: str = Field(min_length=2)
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    skills: list[str] = Field(min_length=1)
    certifications: list[str] = Field(default_factory=list)
    @field_validator("full_name")
    @classmethod
    def check_name(cls, v):
        if v.strip().lower() in PLACEHOLDERS:
            raise ValueError("full_name is a placeholder, not a real name")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if v is not None and not EMAIL_RE.match(v):
            raise ValueError(f"'{v}' is not a valid email address")
        return v

    @field_validator("skills")
    @classmethod
    def clean_skills(cls, v):
        cleaned = list(dict.fromkeys(
            s.strip() for s in v if s.strip() and s.strip().lower() not in PLACEHOLDERS
        ))
        if not cleaned:
            raise ValueError("skills cannot be empty")
        return cleaned


if __name__ == "__main__":
    good = {
        "full_name": "Ananya Sharma",
        "email": "ananya.sharma@example.com",
        "skills": ["Python", "Flask", "Python"],
        "experience": [{"title": "Intern", "company": "TechNova",
                        "start_date": "2025-06", "end_date": "2025-08"}],
    }
    print("VALID  ->", Resume.model_validate(good).skills)

    bad = {
        "full_name": "Rohan Verma",
        "email": "not-an-email",
        "skills": ["Python"],
        "experience": [{"title": "Dev", "company": "X",
                        "start_date": "2023-05", "end_date": "2021-01"}],
    }
    try:
        Resume.model_validate(bad)
    except Exception as e:
        print("INVALID ->", e)