"""
Pymock package propose a base class using Builder design pattern
to create mocked class for testing.
"""

from .mocker import Mock, UnexpectedCall, UnexpectedMethod

all = [Mock, UnexpectedCall, UnexpectedMethod]
