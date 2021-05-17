from typing import Any, List, Tuple

from pydantic import BaseModel

from .exception import NotFullFilled, UnexpectedArguments, UnexpectedCall, UnexpectedMethod


class Mock:
    """
    Mock provides structures and methods to manage your mocked instance.
    """

    class Call:
        class NotFullFilled(BaseModel):
            method: str
            args: List[Any]
            kwargs: dict[str, Any]
            expected: int
            called: int

        """
        Call represent a mocked call.
        """
        __infinite_calls = -1
        __no_calls = 0

        def __init__(self, method: str, *args, **kwargs):
            self.__method = method
            self.__args = args
            self.__kwargs = kwargs

            self.__return_value = None
            self.__raises = None

            self.__nb_calls = 0
            self.__calls_expected = Mock.Call.__infinite_calls

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
                self.__calls_expected == self.__infinite_calls and self.called
            ) or self.__nb_calls == self.__calls_expected

        def _not_full_filled(self) -> NotFullFilled:
            return self.NotFullFilled(
                method=self.__method,
                args=self.__args,
                kwargs=self.__kwargs,
                called=self.__nb_calls,
                expected=self.__calls_expected,
            )

        def _allowed(self) -> bool:
            return (
                self.__calls_expected == self.__infinite_calls
                or self.__nb_calls < self.__calls_expected
            )

        def _match(self, method: str, args: Tuple[any], kwargs: dict) -> bool:
            if not self.__method == method:  # pragma: no-cover
                return False

            for i, arg in enumerate(args):
                if arg != self.__args[i]:
                    return False

            for key, arg in kwargs.items():
                if key not in self.__kwargs and arg is None:
                    continue
                if arg != self.__kwargs[key]:
                    return False

            return True

        def _execute(self):
            if not self._allowed():
                raise UnexpectedCall(self.__method, *self.__args, **self.__kwargs)

            self.__nb_calls += 1

            if self.__raises:
                raise self.__raises

            return self.__return_value

    __calls: dict[str, List[Call]] = {}

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

        call = cls.Call(method, *args, **kwargs)
        cls.__calls[method].append(call)

        return call

    @classmethod
    def reset(cls):
        """
        Reset mock data to avoid border effects.
        """
        cls.__calls = {}

    @classmethod
    def __retrieve_call(cls, method: str, args: Tuple[Any], kwargs: dict) -> Call:
        if method not in cls.__calls:
            raise UnexpectedMethod(method)

        known_mocks = cls.__calls[method]

        last_known = None
        for mock_call in known_mocks:
            if mock_call._match(method, args, kwargs):
                last_known = mock_call
                if mock_call._allowed():
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
        return call._execute()

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
