from typing import Any

import pytest
from src.elmock import Mock, UnexpectedMethod
from src.elmock.exception import NotFullFilled, UnexpectedArguments, UnexpectedCall


class Mocker(Mock):
    def test_smtg(self, p1: str, kp1: Any = None):
        return self.execute("test_smtg", p1, kp1=kp1)

    def test_no_args_no_return(self):
        self.execute("test_no_args_no_return")

    def test_no_args(self) -> Any:
        return self.execute("test_no_args")

    def test_no_return(self, p1: str, kp1: Any = None):
        self.execute("test_no_return", p1, kp1=kp1)


mocked = Mocker()


@pytest.fixture(autouse=True)
def __cleanup_mocks(tmpdir):
    # Setup: fill with any logic you want

    yield  # run test

    # Teardown : fill with any logic you want
    mocked.assert_full_filled()
    mocked.reset()


class TestMock:
    class TestNormalUsages:
        def test_should_execute_nothing_for_empty_method(self):
            mocked_call = mocked.on("test_no_args_no_return")
            mocked.test_no_args_no_return()

            assert mocked_call.called()
            assert mocked_call.full_filled()

        def test_should_return_expected_values(self):
            initial = mocked.on("test_no_args").returns("This is a test")
            assert mocked.test_no_args() == "This is a test"

            # Creating a new instance without number should not be used
            mocked.on("test_no_args").returns("This is another test")
            assert mocked.test_no_args() == "This is a test"

            # Calling .returns again on same initial call should replace it
            initial.returns("This is another test")
            assert mocked.test_no_args() == "This is another test"

        def test_normal_main_use_case(self):
            mocked.on("test_smtg", "val", kp1=True).returns("This is a test")
            assert mocked.test_smtg("val", True) == "This is a test"

            mocked.on("test_smtg", "error", kp1=False).raises(Exception("This is a test"))
            with pytest.raises(Exception):
                mocked.test_smtg("error", False)

        def test_should_be_able_to_raise(self):
            expected = Exception("test")
            mocked_call = mocked.on("test_no_args_no_return").raises(expected)

            with pytest.raises(Exception):
                mocked.test_no_args_no_return()
            assert mocked_call.called()
            assert mocked_call.full_filled()

    class TestRepeatControl:
        def test_should_limit_once(self):
            mocked_call = mocked.on("test_no_args_no_return").once()
            mocked.test_no_args_no_return()

            with pytest.raises(UnexpectedCall):
                mocked.test_no_args_no_return()

            assert mocked_call.called()
            assert mocked_call.full_filled()

        def test_should_limit_twice(self):
            mocked_call = mocked.on("test_no_args_no_return").twice()
            mocked.test_no_args_no_return()
            mocked.test_no_args_no_return()

            with pytest.raises(UnexpectedCall):
                mocked.test_no_args_no_return()

            assert mocked_call.called()
            assert mocked_call.full_filled()

        def test_should_limit_x_times(self):
            mocked_call = mocked.on("test_smtg", "test").times(5)
            mocked.test_smtg("test")
            mocked.test_smtg("test")
            mocked.test_smtg("test")
            mocked.test_smtg("test")
            mocked.test_smtg("test")

            with pytest.raises(UnexpectedCall):
                mocked.test_smtg("test")

            assert mocked_call.called()
            assert mocked_call.full_filled()

            mocked.on("test_smtg", "test").returns("ok")
            # Should pass to next definition after max time reached
            assert mocked.test_smtg("test") == "ok"

        def test_full_filled_should_raise_if_not_full(self):
            call = mocked.on("test_no_args_no_return").times(5)
            mocked.test_no_args_no_return()
            mocked.test_no_args_no_return()
            mocked.test_no_args_no_return()
            mocked.test_no_args_no_return()

            assert call.full_filled() is False
            with pytest.raises(NotFullFilled):
                mocked.assert_full_filled()

            mocked.reset()

        def test_full_filled_should_be_ok_with_correct_x_times(self):
            call = mocked.on("test_no_args_no_return").times(4)
            mocked.test_no_args_no_return()
            mocked.test_no_args_no_return()
            mocked.test_no_args_no_return()
            mocked.test_no_args_no_return()

            assert call.full_filled() is True
            mocked.assert_full_filled()

            mocked.reset()

    class TestMissUsageExceptions:
        def test_should_raise_on_unknown_method(self):
            with pytest.raises(UnexpectedMethod):
                mocked.test_no_args_no_return()

        def test_should_raise_on_invalid_arguments(self):
            mocked_call = mocked.on("test_no_return", "test", kp1="new")
            with pytest.raises(UnexpectedArguments):
                mocked.test_no_return("pasglop", "new")
            assert mocked_call.called() is False

            with pytest.raises(UnexpectedArguments):
                mocked.test_no_return("test", "fun")
            assert mocked_call.called() is False
