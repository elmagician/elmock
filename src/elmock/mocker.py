import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Pattern, Tuple, Type, Union

from pydantic import BaseModel
from shortuuid import ShortUUID  # type: ignore

from .exception import (NotFullFilled, UnexpectedArguments, UnexpectedCall,
                        UnexpectedMethod)


class Mock:
    """
    Mock provides structures and methods to manage your mocked instance.
    """

    class ParameterMatcher(ABC):
        @staticmethod
        @abstractmethod
        def validate(parameter: Any) -> bool:
            """Validate parameter against some rules."""
            raise NotImplementedError()  # pragma: no-cover

    class _ANY(ParameterMatcher):
        @staticmethod
        def validate(_):
            return True

    @staticmethod
    def AnyTyped(expected_types: Tuple) -> ParameterMatcher:
        @staticmethod  # type: ignore
        def validate(parameter: Any) -> bool:
            return isinstance(parameter, expected_types)

        return type("AnyTyped", (Mock.ParameterMatcher,), {"validate": validate})()

    @staticmethod
    def AnyStrMatching(regex: Union[str, Pattern]) -> ParameterMatcher:
        @staticmethod  # type: ignore
        def validate(parameter: Any) -> bool:
            return re.match(regex, str(parameter)) is not None

        return type("AnyTyped", (Mock.ParameterMatcher,), {"validate": validate})()

    ANY = _ANY()

    class Call:
        class NotFullFilled(BaseModel):
            method: str
            args: List[Any]
            kwargs: Dict[str, Any]
            expected: int
            called: int

        """
        Call represent a mocked call.
        """
        __infinite_calls = -1
        __no_calls = 0
        __after: str | None = None

        def __init__(
            self,
            method: str,
            mock_src: Type["Mock"],
            *args,
            after: str | None = None,
            **kwargs
        ):
            self.__method: str = method
            self.__args: Tuple = args
            self.__kwargs: Dict = kwargs

            self.__return_value: Any = None
            self.__raises: Optional[Exception] = None

            self.__nb_calls: int = 0
            self.__calls_expected: int = Mock.Call.__infinite_calls

            self.__origin = mock_src
            self._id = ShortUUID().uuid()
            self.__after = after

        def on(self, method: str, *args, **kwargs) -> "Mock.Call":
            """
            Allow to chain mock calls.
            See `Mock.on` for full documentation.
            """

            return self.__origin.on(method, *args, **kwargs)

        def once(self):
            """
            Indicate that call is expected only once.
            If used with assert_mock_full_filled, it becomes
            the exact number.

            :return: call
            """
            self.times(1)
            return self

        def twice(self):
            """
            Indicate that call is expected only twice.
            If used with assert_mock_full_filled, it becomes
            the exact number.

            :return: call
            """
            self.times(2)
            return self

        def times(self, times: int):
            """
            Indicate that call is expected X times.
            If used with assert_mock_full_filled, it becomes
            the exact number.

            :param times: number of expected calls
            :return: call
            """
            self.__calls_expected = times
            return self

        def returns(self, value: Any):
            """
            Set return value for call.

            /!\\ This operation overwrite existing return value
                or exception raising

            :param value: return value
            :return: call
            """
            self.__return_value = value
            self.__raises = None
            return self

        def raises(self, raises: Exception):
            """
            Set exception to raise for call.

            /!\\ This operation overwrite existing return value
                or exception raising

            :param raises: exception to raise
            :return: call
            """
            self.__return_value = None
            self.__raises = raises
            return self

        def called(self) -> bool:
            """
            Assert call was used
            """
            return self.__nb_calls > 0

        def full_filled(self) -> bool:
            """
            Assert mock was full filled.

            A mock is full filled if it was called and no precise indication
            was provide OR if it was called exactly a provided amount of times.

            Expected amount of times can be sat using `once`, `twice` and `times`
            methods.
            """
            return (
                self.__calls_expected == self.__infinite_calls  # type: ignore
                and self.called
                or self.__nb_calls == self.__calls_expected
            )

        def before(self, method: str, *args, **kwargs) -> "Mock.Call":
            """
            Ensure call is made before another on similar method
            """

            call = self.__origin.on(method, *args, **kwargs)
            call.__after = self._id

            return call

        def _not_full_filled(self) -> NotFullFilled:
            return self.NotFullFilled(
                method=self.__method,
                args=self.__args,
                kwargs=self.__kwargs,
                called=self.__nb_calls,
                expected=self.__calls_expected,
            )

        def _allowed(self, latest_call_id: str | None) -> bool:
            return (
                self.__calls_expected == self.__infinite_calls
                or self.__nb_calls < self.__calls_expected
            ) and (self.__after is None or latest_call_id == self.__after)

        def _match(self, method: str, args: Tuple, kwargs: dict) -> bool:
            if not self.__method == method:  # pragma: no-cover
                return False

            args_to_check_in_kwargs = []
            unused_args = list(self.__args)

            nb_args = len(self.__args)
            for i, arg in enumerate(args):
                if i < nb_args:
                    expected = self.__args[i]

                    if isinstance(expected, Mock.ParameterMatcher):
                        if not expected.validate(arg):
                            return False
                    elif arg != expected:
                        return False

                    unused_args.remove(expected)
                else:
                    args_to_check_in_kwargs.append(arg)

            unmatched_kwargs = []
            for key, arg in kwargs.items():
                if key not in self.__kwargs:
                    if arg is None:
                        continue

                    if arg in unused_args:
                        unused_args.remove(arg)
                    else:
                        unmatched_kwargs.append(arg)

                expected = self.__kwargs.get(key)
                if isinstance(expected, Mock.ParameterMatcher):
                    if not expected.validate(arg):
                        return False

                elif arg != expected:
                    return False

            for arg in args_to_check_in_kwargs:
                if arg in unmatched_kwargs:
                    unmatched_kwargs.remove(arg)
                else:
                    return False

            return args_to_check_in_kwargs == []

        def _execute(self, latest_call_id: str | None):
            if not self._allowed(latest_call_id):
                raise UnexpectedCall(
                    self.__method,
                    latest_call_id,
                    self.__after,
                    *self.__args,
                    **self.__kwargs
                )

            self.__nb_calls += 1

            if self.__raises:
                raise self.__raises

            return self.__return_value

    __calls: Dict[str, List[Call]] = {}
    __latest_called: List[str] = []

    @classmethod
    def on(cls, method: str, *args, **kwargs) -> Call:
        """
        Start a new expected call matching method and arguments.

        :param method: name of method to mock
        :param args: expected argument to match
        :param kwargs: expected kwargs to match
        :return: mocked call to configure
        """
        if method not in cls.__calls:
            cls.__calls[method] = []

        call = cls.Call(method, cls, *args, **kwargs)
        cls.__calls[method].append(call)

        return call

    @classmethod
    def reset(cls):
        """
        Reset mock data to avoid border effects.
        """
        cls.__calls = {}
        cls.__latest_called = []

    @classmethod
    def __retrieve_call(cls, method: str, args: Tuple, kwargs: dict) -> Call:
        if method not in cls.__calls:
            raise UnexpectedMethod(method)

        known_mocks = cls.__calls[method]

        last_known = None
        for mock_call in known_mocks:
            if mock_call._match(method, args, kwargs):
                last_known = mock_call
                if mock_call._allowed(cls.__latest_called[-1] if cls.__latest_called else None):
                    return mock_call

        if last_known is not None:
            return last_known

        raise UnexpectedArguments(method, args, kwargs)

    @classmethod
    def execute(cls, method: str, *args, **kwargs) -> Any:
        """
        Retrieve call from known mocked call and try to execute it.

        :param method: method name
        :param args: arguments to match
        :param kwargs: named arguments to match
        :return: mocked value to return if provided
        :raises Exception: mocked Exception to return if provided
        """
        call = cls.__retrieve_call(method, args, kwargs)
        res = call._execute(cls.__latest_called[-1] if cls.__latest_called else None)
        cls.__latest_called.append(call._id)
        return res

    @classmethod
    def assert_full_filled(cls) -> None:
        """
        Check if all called where full filled.
        If not raise NotFullFilled error.

        :raises NotFullFilled: if some calls where not full filled
        """
        incomplete: List[Mock.Call.NotFullFilled] = []
        for calls in cls.__calls.values():
            incomplete.extend(
                [call._not_full_filled() for call in calls if not call.full_filled()]
            )

        if incomplete:
            raise NotFullFilled(incomplete)
