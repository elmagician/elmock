from typing import Any

import pytest

from src.elmock import Mock, UnexpectedMethod
from src.elmock.exception import (NotFullFilled, UnexpectedArguments,
                                  UnexpectedCall)


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

            mocked.on("test_smtg", "error", kp1=False).raises(
                Exception("This is a test")
            )
            with pytest.raises(Exception):
                mocked.test_smtg("error", False)

        def test_should_be_able_to_raise(self):
            expected = Exception("test")
            mocked_call = mocked.on("test_no_args_no_return").raises(expected)

            with pytest.raises(Exception):
                mocked.test_no_args_no_return()
            assert mocked_call.called()
            assert mocked_call.full_filled()

        def test_should_be_chainable(self):
            expected = Exception("test")

            (
                mocked.on("test_no_args_no_return")
                .raises(expected)
                .on("test_smtg", "error", kp1="ok")
                .on("test_smtg", "nother", kp1=True)
            )

            with pytest.raises(Exception):
                mocked.test_no_args_no_return()

            mocked.test_smtg("error", "ok")
            mocked.test_smtg("nother", kp1=True)

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

        def test_should_not_match_invalid_kwargs_as_args(self):
            mocked.on("test_smtg", "test", kp1="test")

            with pytest.raises(UnexpectedArguments):
                mocked.test_smtg("test", "testa")

            with pytest.raises(UnexpectedArguments):
                mocked.test_smtg("test", kp1="testa")

        def test_should_not_match_invalid_args_as_kwargs(self):
            mocked.on("test_smtg", "test", kp1="test")

            with pytest.raises(UnexpectedArguments):
                mocked.test_smtg(p1="testa", kp1="test")

            with pytest.raises(UnexpectedArguments):
                mocked.test_smtg("testa", kp1="test")

    class TestCallLinks:
        def test_should_allowed_linked_calls(self):
            (
                mocked.on("test_no_args")
                .returns("Sparta")
                .before("test_no_args_no_return")
                .before("test_smtg", "a", kp1="b")
                .returns("Twice")
                .before("test_smtg", "c")
                .returns("Last")
            )

            assert mocked.test_no_args() == "Sparta"
            mocked.test_no_args_no_return()
            assert mocked.test_smtg("a", "b") == "Twice"
            assert mocked.test_smtg("c") == "Last"

        def test_should_allowed_linked_calls_on_same_methods(self):
            (
                mocked.on("test_no_args")
                .returns("Sparta")
                .before("test_no_args_no_return")
                .before("test_smtg", "a", kp1="b")
                .returns("Twice")
                .before("test_smtg", "c", on_same_method=True)
                .returns("Last")
            )

            assert mocked.test_no_args() == "Sparta"
            mocked.test_no_args_no_return()
            assert mocked.test_smtg("a", "b") == "Twice"
            assert mocked.test_smtg("c") == "Last"

            mocked.reset()

            (
                mocked.on("test_no_args")
                .returns("Sparta")
                .before("test_no_args_no_return")
                .before("test_smtg", "a", kp1="b")
                .returns("Twice")
                .before("test_smtg", "c", on_same_method=True)
                .returns("Last")
                .before("test_smtg", "d", on_same_method=True)
                .returns("A")
            )

            assert mocked.test_no_args() == "Sparta"
            mocked.test_no_args_no_return()
            assert mocked.test_smtg("a", "b") == "Twice"

            assert mocked.test_no_args() == "Sparta"
            mocked.test_no_args_no_return()
            assert mocked.test_smtg("c") == "Last"

            assert mocked.test_no_args() == "Sparta"
            mocked.test_no_args_no_return()
            assert mocked.test_smtg("d") == "A"

        def test_should_not_allow_linked_call_if_ancestor_is_invalid(self):
            (
                mocked.on("test_no_args")
                .returns("Sparta")
                .before("test_no_args_no_return")
                .before("test_smtg", "a", kp1="b")
                .returns("Twice")
                .before("test_smtg", "c")
                .returns("Last")
            )

            with pytest.raises(UnexpectedCall):
                mocked.test_no_args_no_return()

            with pytest.raises(UnexpectedCall):
                mocked.test_smtg("a", "b")

            with pytest.raises(UnexpectedCall):
                assert mocked.test_no_args() == "Sparta"
                mocked.test_smtg("a", "b")

            with pytest.raises(UnexpectedCall):
                assert mocked.test_no_args() == "Sparta"
                mocked.test_smtg("c")

            with pytest.raises(UnexpectedCall):
                (
                    mocked.on("test_no_args")
                    .returns("Sparta")
                    .before("test_no_args_no_return")
                    .before("test_smtg", "a", kp1="b")
                    .returns("Twice")
                    .before("test_smtg", "c")
                    .returns("Last")
                )

                assert mocked.test_no_args() == "Sparta"
                mocked.test_no_args_no_return()
                assert mocked.test_smtg("c") == "Last"

        def test_should_not_allow_invalid_linked_calls_on_same_methods(self):
            (
                mocked.on("test_no_args")
                .returns("Sparta")
                .before("test_no_args_no_return")
                .before("test_smtg", "a", kp1="b")
                .returns("Twice")
                .before("test_smtg", "c", on_same_method=True)
                .returns("Last")
                .before("test_smtg", "d", on_same_method=True, kp1="c")
                .returns("A")
            )
            mocked.test_no_args()
            mocked.test_no_args_no_return()
            with pytest.raises(UnexpectedCall) as exc:
                mocked.test_smtg("c") == "Last"
            assert "Broken linked called" in exc.value.message

            mocked.test_smtg("a", "b")

            exc = None
            with pytest.raises(UnexpectedCall) as exc:
                mocked.test_smtg("d", kp1="c") == "A"

            assert "Broken linked called" in exc.value.message

            with pytest.raises(UnexpectedCall):
                mocked.test_smtg("a", "b")

            mocked.test_no_args()
            mocked.test_no_args_no_return()
            mocked.test_smtg("a", "b")
            with pytest.raises(UnexpectedCall) as exc:
                mocked.test_smtg("d", kp1="c") == "A"
            assert "Broken linked called" in exc.value.message

    class TestNonAbsoluteParameters:
        class TestInArgs:
            def test_ANY_should_match_anything(self):
                mocked_call = mocked.on("test_smtg", Mock.ANY, kp1="test")

                mocked.test_smtg("test", "test")
                mocked.test_smtg(124, "test")
                mocked.test_smtg({"blah": "test"}, "test")
                mocked.test_smtg(True, "test")
                mocked.test_smtg({1, 2, 5}, "test")

                assert mocked_call.called()
                assert mocked_call.full_filled()
                mocked.reset()

            def test_AnyTyped_should_match_provided_types(self):
                mocked_call = mocked.on(
                    "test_smtg", Mock.AnyTyped((str, dict)), kp1="test"
                )

                mocked.test_smtg("test", "test")
                mocked.test_smtg({"blah": "test"}, "test")

                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg(124, "test")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg(True, "test")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg({1, 2, 5}, "test")

                assert mocked_call.called()
                assert mocked_call.full_filled()
                mocked.reset()

            def test_AnyStrMatching_should_match_any_str_matching_pattern(self):
                mocked_call = mocked.on(
                    "test_smtg", Mock.AnyStrMatching(r"[1-4]49[0-9].*"), kp1="test"
                )

                mocked.test_smtg("3495abnug", "test")
                mocked.test_smtg(3495, "test")

                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg(124, "test")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg(True, "test")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("a1490", "test")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("1590", "test")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg({1, 2, 5}, "test")

                assert mocked_call.called()
                assert mocked_call.full_filled()
                mocked.reset()

        class TestInKwArgs:
            def test_ANY_should_match_anything(self):
                mocked_call = mocked.on("test_smtg", "test", kp1=Mock.ANY)

                mocked.test_smtg("test", "test")
                mocked.test_smtg("test", 124)
                mocked.test_smtg("test", {"blah": "test"})
                mocked.test_smtg("test", True)
                mocked.test_smtg("test", {1, 2, 5})

                assert mocked_call.called()
                assert mocked_call.full_filled()
                mocked.reset()

            def test_AnyTyped_should_match_provided_types(self):
                mocked_call = mocked.on(
                    "test_smtg", "test", kp1=Mock.AnyTyped((str, dict))
                )

                mocked.test_smtg("test", "test")
                mocked.test_smtg("test", {"blah": "test"})

                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", 124)
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", True)
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", {1, 2, 5})

                assert mocked_call.called()
                assert mocked_call.full_filled()
                mocked.reset()

            def test_AnyStrMatching_should_match_any_str_matching_pattern(self):
                mocked_call = mocked.on(
                    "test_smtg", "test", kp1=Mock.AnyStrMatching(r"[1-4]49[0-9].*")
                )

                mocked.test_smtg("test", "3495abnug")
                mocked.test_smtg("test", 3495)

                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", 124)
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", True)
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", "a1490")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", "1590")
                with pytest.raises(UnexpectedArguments):
                    mocked.test_smtg("test", {1, 2, 5})

                assert mocked_call.called()
                assert mocked_call.full_filled()
                mocked.reset()

    class TestSpecialCases:
        def test_should_match_kwargs_passed_as_args(self):
            mocked_call = mocked.on("test_smtg", "test", kp1="test")

            mocked.test_smtg("test", "test")

            assert mocked_call.called()
            assert mocked_call.full_filled()
            mocked.reset()

            mocked_call = mocked.on("test_smtg", "test", "test")

            with pytest.raises(UnexpectedArguments):
                mocked.test_smtg("test", "test")

            mocked.reset()

            mocked_call = mocked.on("test_smtg", p1="test", kp1="test")

            with pytest.raises(UnexpectedArguments):
                mocked.test_smtg("test", "test")

            mocked.reset()

        def test_should_match_args_passed_as_kwargs(self):
            mocked_call = mocked.on("test_smtg", "test", kp1="test")

            mocked.test_smtg(p1="test", kp1="test")

            assert mocked_call.called()
            assert mocked_call.full_filled()
