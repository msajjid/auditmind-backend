from django.contrib import admin

from audit_api import models


@admin.register(models.Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "organization", "status", "created_at")
    list_filter = ("status", "organization")
    search_fields = ("id", "title", "description")
    ordering = ("-created_at",)


@admin.register(models.AiPipelineRun)
class AiPipelineRunAdmin(admin.ModelAdmin):
    list_display = ("id", "pipeline_type", "status", "started_at", "finished_at")
    list_filter = ("pipeline_type", "status")
    search_fields = ("id",)
    ordering = ("-started_at",)


@admin.register(models.AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ("id", "agent_name", "agent_version", "status", "started_at", "finished_at")
    list_filter = ("agent_name", "status")
    search_fields = ("id", "agent_name", "agent_version")
    ordering = ("-started_at",)


@admin.register(models.AgentStepLog)
class AgentStepLogAdmin(admin.ModelAdmin):
    list_display = ("id", "agent_run", "step_name", "status", "started_at", "finished_at")
    list_filter = ("status", "step_name")
    search_fields = ("id", "step_name", "agent_run__id")
    ordering = ("started_at",)


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "organization", "evidence", "created_at")
    list_filter = ("event_type",)
    search_fields = ("id", "event_type", "evidence__id", "organization__id")
    ordering = ("-created_at",)


@admin.register(models.ClassifierOutput)
class ClassifierOutputAdmin(admin.ModelAdmin):
    list_display = ("id", "evidence", "pipeline_run", "confidence", "created_at")
    search_fields = ("id", "evidence__id", "pipeline_run__id")
    ordering = ("-created_at",)


@admin.register(models.PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "version", "created_at")
    search_fields = ("name", "version", "id")
    ordering = ("-created_at",)


@admin.register(models.ModelRegistry)
class ModelRegistryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "provider", "version", "model_type", "embedding_dims", "created_at")
    search_fields = ("name", "provider", "version", "id")
    list_filter = ("provider", "model_type")
    ordering = ("-created_at",)
