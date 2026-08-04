"""
Run every factory in the project.

A new factory is picked up automatically, and one broken by a model change fails
here under its own name instead of somewhere inside an unrelated domain test.
"""

import importlib
import pkgutil

import pytest
from factory.django import DjangoModelFactory

import apps


def discover_factories() -> list[type]:
    found: list[type] = []
    for module_info in pkgutil.iter_modules(apps.__path__):
        try:
            module = importlib.import_module(f"apps.{module_info.name}.factories")
        except ModuleNotFoundError:
            continue
        for attribute in vars(module).values():
            if (
                isinstance(attribute, type)
                and issubclass(attribute, DjangoModelFactory)
                and attribute is not DjangoModelFactory
                and attribute.__module__ == module.__name__
            ):
                found.append(attribute)
    return found


FACTORIES = discover_factories()


def test_at_least_one_factory_is_discovered():
    # Guards the discovery itself: a rename that finds nothing would otherwise
    # turn this whole module into a silent no-op.
    assert FACTORIES


@pytest.mark.django_db
@pytest.mark.parametrize("factory_class", FACTORIES, ids=lambda f: f.__name__)
def test_factory_creates_a_valid_object(factory_class):
    instance = factory_class()

    assert instance.pk is not None
    instance.full_clean(exclude=["password"])


@pytest.mark.django_db
@pytest.mark.parametrize("factory_class", FACTORIES, ids=lambda f: f.__name__)
def test_factory_can_build_a_batch(factory_class):
    """Unique constraints have to survive more than one object (Sequence, not a constant)."""
    objects = factory_class.create_batch(3)
    assert len({obj.pk for obj in objects}) == 3
