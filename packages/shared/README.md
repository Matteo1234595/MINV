# Shared Schemas

This package hosts JSON schema artifacts shared between the API and web apps.

## Layout

- `schemas/` contains JSON Schema files.
- `samples/` contains CSV templates for ingestion endpoints.

## Usage

Consume schemas from tooling or code generation pipelines as needed. Each schema
includes a `$id` field for stable references.
