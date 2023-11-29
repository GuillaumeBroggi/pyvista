"""Functions that check the type and/or value of inputs.

.. versionadded:: 0.43.0

A ``check`` function typically:

* Performs a simple validation on a single input variable.
* Raises an error if the check fails due to invalid input.
* Does not modify input or return anything.

"""
from collections.abc import Iterable, Sequence
from numbers import Number, Real
from typing import Any, List, Literal, Optional, Sized, Tuple, Union, cast, get_args, get_origin

import numpy as np
import numpy.typing as npt

# Similar definitions to numpy._typing._shape but with modifications:
#  - explicit support for empty tuples `()`
#  - strictly uses tuples for indexing
#  - our ShapeLike definition includes single integers (numpy's does not)
ShapeLike = Union[int, Tuple[()], Tuple[int, ...]]
Shape = Union[Tuple[()], Tuple[int, ...]]

from pyvista.core._typing_core import FloatVector, IntVector
from pyvista.core.utilities.arrays import cast_to_ndarray


def check_is_subdtype(
    input_obj: Union[npt.DTypeLike, npt.ArrayLike],
    base_dtype: Union[npt.DTypeLike, Sequence],
    /,
    *,
    name: str = 'Input',
):
    """Check if an input's data-type is a subtype of another data-type(s).

    Parameters
    ----------
    input_obj : numpy.typing.DTypeLike | numpy.typing.ArrayLike
        ``dtype`` object (or object coercible to one) or an array-like object.
        If array-like, the dtype of the array is used.

    base_dtype : numpy.typing.DTypeLike | Sequence[numpy.typing.DTypeLike]
        ``dtype``-like object or a sequence of ``dtype``-like objects. The ``input_obj``
        must be a subtype of this value. If a sequence, ``input_obj`` must be a
        subtype of at least one of the specified dtypes.

    name : str, default: "Input"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If ``input_obj`` is not a subtype of ``base_dtype``.

    See Also
    --------
    check_is_real
    check_is_number

    Examples
    --------
    Check if ``int`` is a subtype of ``np.integer``.

    >>> import numpy as np
    >>> from pyvista.core import validate
    >>> validate.check_is_subdtype(float, np.floating)

    Check from multiple allowable dtypes.

    >>> validate.check_is_subdtype(int, [np.integer, np.floating])

    Check an array's dtype.

    >>> arr = np.array([1, 2, 3], dtype='uint8')
    >>> validate.check_is_subdtype(arr, np.integer)

    """
    if isinstance(input_obj, np.dtype):
        pass
    elif isinstance(input_obj, np.ndarray):
        input_obj = input_obj.dtype
    else:
        input_obj = np.dtype(cast(npt.DTypeLike, input_obj))
    input_obj = cast(np.dtype, input_obj)

    if not isinstance(base_dtype, (list, tuple)):
        base_dtype = [base_dtype]
    for d in base_dtype:
        if np.issubdtype(input_obj, d):
            return
    msg = f"{name} has incorrect dtype of '{input_obj}'. "
    if len(base_dtype) == 1:
        msg += f"The dtype must be a subtype of {base_dtype[0]}."
    else:
        msg += f"The dtype must be a subtype of at least one of \n{base_dtype}."
    raise TypeError(msg)


def check_is_numeric(arr: npt.ArrayLike, /, *, name: str = "Array"):
    """Check if an array is float, integer, or complex type.

    Notes
    -----
    Arrays with ``infinity`` or ``NaN`` values are numeric  and
    will not raise an error. Use :func:`check_is_finite` to check for
    finite values.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If the array is not numeric.

    See Also
    --------
    check_is_real
    check_is_finite

    Examples
    --------
    Check if an array is numeric.

    >>> from pyvista.core import validate
    >>> validate.check_is_numeric([1, 2.0, 3 + 3j])

    """
    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)

    # Return early for common cases
    if arr.dtype.type in [np.int32, np.int64, np.float32, np.float64, np.complex_]:
        return
    try:
        check_is_subdtype(arr, np.number, name=name)
    except TypeError as e:
        raise TypeError(f"{name} must be numeric.") from e


def check_is_real(arr: npt.ArrayLike, /, *, name: str = "Array"):
    """Check if an array has real numbers, i.e. float or integer type.

    Notes
    -----
    Arrays with ``infinity`` or ``NaN`` values are considered real and
    will not raise an error. Use :func:`check_is_finite` to check for
    finite values.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If the array does not have real numbers.

    See Also
    --------
    check_is_numeric
        Similar function which allows complex numbers.
    check_is_scalar
        Similar function for a single number or 0-dimensional ndarrays.
    check_is_finite

    Examples
    --------
    Check if an array has real numbers.

    >>> from pyvista.core import validate
    >>> validate.check_is_real([1, 2, 3])

    """
    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)

    # Return early for common cases
    if arr.dtype.type in [np.int32, np.int64, np.float32, np.float64]:
        return

    # Do not use np.isreal as it will fail in some cases (e.g. scalars).
    # Check dtype directly instead
    try:
        check_is_subdtype(arr, (np.floating, np.integer), name=name)
    except TypeError as e:
        raise TypeError(f"{name} must have real numbers.") from e


def check_is_sorted(
    arr: npt.ArrayLike,
    /,
    *,
    ascending: bool = True,
    strict: bool = False,
    axis: int = -1,
    name: str = "Array",
):
    """Check if an array's values are sorted.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    ascending : bool, default: True
        If ``True``, check if the array's elements are in ascending order.
        If ``False``, check if the array's elements are in descending order.

    strict : bool, default: False
        If ``True``, the array's elements must be strictly increasing (if
        ``ascending=True``) or strictly decreasing (if ``ascending=False``).
        Effectively, this means the array must be sorted *and* its values
        must be unique.

    axis : int | None, default: -1
        Axis along which to check sorting. If ``None``, the array is flattened
        before checking. The default is ``-1``, which checks sorting along the
        last axis.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If the array is not sorted in ascending order.

    See Also
    --------
    check_is_in_range

    Examples
    --------
    Check if an array's values are sorted,

    >>> from pyvista.core import validate
    >>> validate.check_is_sorted([1, 2, 3])

    """
    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)

    if arr.ndim == 0:
        # Indexing will fail for scalars, so return early
        return

    # Validate axis
    if axis is None:
        # Emulate np.sort(), which flattens array when axis is None
        arr = arr.flatten()
        axis = -1
    else:
        if not axis == -1:
            # Validate axis
            check_is_number(axis, name="Axis")
            check_is_integerlike(axis, name="Axis")
            axis = int(axis)
            try:
                check_is_in_range(axis, rng=[-arr.ndim, arr.ndim - 1], name="Axis")
            except ValueError:
                raise ValueError(f"Axis {axis} is out of bounds for ndim {arr.ndim}.")
        if axis < 0:
            # Convert to positive axis index
            axis = arr.ndim + axis

    # Create slicers to get a view along an axis
    # Create two slicers to compare consecutive elements with each other
    first = [slice(None)] * arr.ndim
    first[axis] = slice(None, -1)
    first = tuple(first)  # type: ignore

    second = [slice(None)] * arr.ndim
    second[axis] = slice(1, None)
    second = tuple(second)  # type: ignore

    if ascending and not strict:
        is_sorted = np.all(arr[first] <= arr[second])  # type: ignore
    elif ascending and strict:
        is_sorted = np.all(arr[first] < arr[second])  # type: ignore
    elif not ascending and not strict:
        is_sorted = np.all(arr[first] >= arr[second])  # type: ignore
    else:  # not ascending and strict
        is_sorted = np.all(arr[first] > arr[second])  # type: ignore
    if not is_sorted:
        if arr.size <= 4:
            # Show the array's elements in error msg if array is small
            msg_body = f"{arr}"
        else:
            msg_body = f"with {arr.size} elements"
        order = "ascending" if ascending else "descending"
        strict = "strict " if strict else ""  # type: ignore
        raise ValueError(f"{name} {msg_body} must be sorted in {strict}{order} order.")


def check_is_finite(arr: npt.ArrayLike, /, *, name: str = "Array"):
    """Check if an array has finite values, i.e. no NaN or Inf values.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If the array has any ``Inf`` or ``NaN`` values.

    See Also
    --------
    check_is_real

    Examples
    --------
    Check if an array's values are finite.

    >>> from pyvista.core import validate
    >>> validate.check_is_finite([1, 2, 3])

    """
    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must have finite values.")


def check_is_integerlike(arr: npt.ArrayLike, /, *, strict: bool = False, name: str = "Array"):
    """Check if an array has integer or integer-like float values.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    strict : bool, default: False
        If ``True``, the array's data must be a subtype of ``np.integer``
        (i.e. float types are not allowed).

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If any element's value differs from its floor.

    TypeError
        If ``strict=True`` and the array's dtype is not integral.

    See Also
    --------
    check_is_nonnegative
    check_is_subdtype

    Examples
    --------
    Check if an array has integer-like values.

    >>> from pyvista.core import validate
    >>> validate.check_is_integerlike([1.0, 2.0])

    """
    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)
    if strict:
        try:
            check_is_subdtype(arr, np.integer)
        except TypeError:
            raise
    elif not np.array_equal(arr, np.floor(arr)):
        raise ValueError(f"{name} must have integer-like values.")


def check_is_nonnegative(arr: npt.ArrayLike, /, *, name: str = "Array"):
    """Check if an array's elements are all nonnegative.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If the array has any negative values.

    See Also
    --------
    check_is_greater_than
    check_is_less_than

    Examples
    --------
    Check if an array's values are non-negative.

    >>> from pyvista.core import validate
    >>> validate.check_is_nonnegative([1, 2, 3])

    """
    try:
        check_is_greater_than(arr, 0, strict=False, name=name)
    except ValueError:
        raise


def check_is_greater_than(
    arr: npt.ArrayLike, /, value: float, *, strict: bool = True, name: str = "Array"
):
    """Check if an array's elements are all greater than some value.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    value : float
        Value which the array's elements must be greater than.

    strict : bool, default: True
        If ``True``, the array's value must be strictly greater than ``value``.
        Otherwise, values must be greater than or equal to ``value``.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If not all array elements are greater than (or equal to if
        ``strict=True``) the specified value.

    See Also
    --------
    check_is_less_than
    check_is_in_range
    check_is_nonnegative

    Examples
    --------
    Check if an array's values are greater than 0.

    >>> from pyvista.core import validate
    >>> validate.check_is_greater_than([1, 2, 3], value=0)

    """
    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)
    check_is_number(value)
    check_is_real(value)
    if strict and not np.all(arr > value):
        raise ValueError(f"{name} values must all be greater than {value}.")
    elif not np.all(arr >= value):
        raise ValueError(f"{name} values must all be greater than or equal to {value}.")


def check_is_less_than(
    arr: npt.ArrayLike, /, value: float, *, strict: bool = True, name: str = "Array"
):
    """Check if an array's elements are all less than some value.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    value : float
        Value which the array's elements must be less than.

    strict : bool, default: True
        If ``True``, the array's value must be strictly less than
        ``value``. Otherwise, values must be less than or equal to
        ``value``.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If not all array elements are less than (or equal to if
        ``strict=True``) the specified value.

    See Also
    --------
    check_is_greater_than
    check_is_in_range
    check_is_nonnegative

    Examples
    --------
    Check if an array's values are less than 0.

    >>> from pyvista.core import validate
    >>> validate.check_is_less_than([-1, -2, -3], value=0)

    """
    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)
    check_is_number(value)
    check_is_real(value)
    if strict and not np.all(arr < value):
        raise ValueError(f"{name} values must all be less than {value}.")
    elif not np.all(arr <= value):
        raise ValueError(f"{name} values must all be less than or equal to {value}.")


def check_is_in_range(
    arr: npt.ArrayLike,
    /,
    rng: FloatVector,
    *,
    strict_lower: bool = False,
    strict_upper: bool = False,
    name: str = "Array",
):
    """Check if an array's values are all within a specific range.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    rng : FloatVector, optional
        Vector with two elements ``[min, max]`` specifying the minimum
        and maximum data values allowed, respectively. By default, the
        range endpoints are inclusive, i.e. values must be >= min
        and <= max. Use ``strict_lower`` and/or ``strict_upper``
        to further restrict the allowable range. Use ``np.inf`` or
        ``-np.inf`` to specify open intervals, e.g. ``[0, np.inf]``.

    strict_lower : bool, default: False
        Enforce a strict lower bound for the range, i.e. array values
        must be strictly greater than the minimum.

    strict_upper : bool, default: False
        Enforce a strict upper bound for the range, i.e. array values
        must be strictly less than the maximum.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If any array value is outside the specified range.

    See Also
    --------
    check_is_less_than
    check_is_greater_than

    Examples
    --------
    Check if `an array's values are in the range ``[0, 1]``.

    >>> from pyvista.core import validate
    >>> validate.check_is_in_range([0, 0.5, 1], rng=[0, 1])

    """
    rng_ = cast_to_ndarray(rng)
    check_has_shape(rng_, 2, name="Range")
    check_is_sorted(rng_, name="Range")

    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)
    try:
        check_is_greater_than(arr, rng_[0], strict=strict_lower, name=name)
        check_is_less_than(arr, rng_[1], strict=strict_upper, name=name)
    except ValueError:
        raise


def check_has_shape(
    arr: npt.ArrayLike,
    /,
    shape: Union[ShapeLike, List[ShapeLike]],
    *,
    name: str = "Array",
):
    """Check if an array has the specified shape.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    shape : ShapeLike | list[ShapeLike], optional
        A single shape or a list of any allowable shapes. If an integer,
        ``i``, the shape is interpreted as ``(i,)``. Use a value of
        -1 for any dimension where its size is allowed to vary, e.g.
        ``(-1,3)`` if any Nx3 array is allowed. Use ``()`` for the
        shape of scalar values (i.e. 0-dimensional). If a list, the
        array must have at least one of the specified shapes.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If the array does not have any of the specified shape(s).

    See Also
    --------
    check_has_length

    Examples
    --------
    Check if an array is one-dimensional.

    >>> import numpy as np
    >>> from pyvista.core import validate
    >>> validate.check_has_shape([1, 2, 3], shape=(-1))

    Check if an array is one-dimensional or a scalar.

    >>> validate.check_has_shape(1, shape=[(), (-1)])

    Check if an array is 3x3 or 4x4.

    >>> validate.check_has_shape(np.eye(3), shape=[(3, 3), (4, 4)])

    """

    def _shape_is_allowed(a: Shape, b: Shape) -> bool:
        # a: array's actual shape
        # b: allowed shape (may have -1)
        if len(a) == len(b) and all(map(lambda x, y: True if x == y else y == -1, a, b)):
            return True
        else:
            return False

    arr = arr if isinstance(arr, np.ndarray) else cast_to_ndarray(arr)

    if not isinstance(shape, list):
        shape = [shape]

    array_shape = arr.shape
    for input_shape in shape:
        input_shape = _validate_shape_value(input_shape)
        if _shape_is_allowed(array_shape, input_shape):
            return

    msg = f"{name} has shape {arr.shape} which is not allowed. "
    if len(shape) == 1:
        msg += f"Shape must be {shape[0]}."
    else:
        msg += f"Shape must be one of {shape}."
    raise ValueError(msg)


def check_is_number(
    num: Union[float, int, complex, np.number, Number],
    /,
    *,
    definition: Literal['abstract', 'builtin', 'numpy'] = 'abstract',
    must_be_real=True,
    name: str = 'Object',
):
    """Check if an object is a number.

    By default, the number must be an instance of the abstract base class :class:`numbers.Real`.
    Optionally, the number can also be complex. The definition can also be restricted
    to strictly check if the number is a built-in numeric type (e.g. ``int``, ``float``)
    or numpy numeric data types (e.g. ``np.floating``, ``np.integer``).

    Notes
    -----
    - This check fails for instances of :class:`numpy.ndarray`. Use :func:`check_is_scalar`
      instead to also allow for 0-dimensional arrays.
    - Values such as ``float('inf')`` and ``float('NaN')`` are valid numbers and
      will not raise an error. Use :func:`check_is_finite` to check for finite values.

    .. warning::

        - Some NumPy numeric data types are subclasses of the built-in types whereas other are
          not. For example, ``numpy.float_`` is a subclass of ``float`` and ``numpy.complex_``
          is a subclass ``complex``. However, ``numpy.int_`` is not a subclass of ``int`` and
          ``numpy.bool_`` is not a subclass of ``bool``.
        - The built-in ``bool`` type is a subclass of ``int`` whereas NumPy's``.bool_`` type
          is not a subclass of ``np.int_`` (``np.bool_`` is not a numeric type).

        This can lead to unexpected results:

        - This check will always fail for ``np.bool_`` types.
        - This check will pass for ``np.float_`` or ``np.complex_``, even if
          ``definition='builtin'``.

    Parameters
    ----------
    num : float | int | complex | numpy.number | Number
        Number to check.

    definition : str, default: 'abstract'
        Control the base class(es) to use when checking the number's type. Must be
        one of:

        - ``'abstract'`` : number must be an instance of one of the abstract types
          in :py:mod:`numbers`.
        - ``'builtin'`` : number must be an instance of one of the built-in numeric
          types.
        - ``'numpy'`` : number must be an instance of NumPy's data types.

    must_be_real : bool, default: True
        If ``True``, the number must be real, i.e. an integer or
        floating type. Set to ``False`` to allow complex numbers.

    name : str, default: "Object"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If input is not an instance of a numeric type.

    See Also
    --------
    check_is_scalar
        Similar function which allows 0-dimensional ndarrays.
    check_is_numeric
        Similar function for any dimensional array of numbers.
    check_is_real
        Similar function for any dimensional array of real numbers.
    check_is_finite


    Examples
    --------
    Check if a float is a number.
    >>> from pyvista.core import validate
    >>> num = 42.0
    >>> type(num)
    <class 'float'>
    >>> validate.check_is_number(num)

    Check if an element of a NumPy array is a number.

    >>> import numpy as np
    >>> num_array = np.array([1, 2, 3])
    >>> num = num_array[0]
    >>> type(num)
    <class 'numpy.int64'>
    >>> validate.check_is_number(num)

    Check if a complex number is a number.
    >>> num = 1 + 2j
    >>> type(num)
    <class 'complex'>
    >>> validate.check_is_number(num, must_be_real=False)

    """
    check_is_string_in_iterable(definition, ['abstract', 'builtin', 'numpy'])

    valid_type: Any
    if definition == 'abstract':
        valid_type = Real if must_be_real else Number
    elif definition == 'builtin':
        valid_type = (float, int) if must_be_real else (float, int, complex)
    elif definition == 'numpy':
        valid_type = (np.floating, np.integer) if must_be_real else np.number
    else:
        raise NotImplementedError  # pragma: no cover

    try:
        check_is_instance(num, valid_type, allow_subclass=True, name=name)
    except TypeError:
        raise


def check_is_string(obj: str, /, *, allow_subclass: bool = True, name: str = 'Object'):
    """Check if an object is an instance of ``str``.

    Parameters
    ----------
    obj : str
        Object to check.

    allow_subclass : bool, default: True
        If ``True``, the object's type must be ``str`` or a subclass of
        ``str``. Otherwise, subclasses are not allowed.

    name : str, default: "Object"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If input is not an instance of ``str``.

    See Also
    --------
    check_is_string_in_iterable
    check_is_iterable_of_strings
    check_is_sequence
    check_is_instance

    Examples
    --------
    Check if an object is a string.

    >>> from pyvista.core import validate
    >>> validate.check_is_string("eggs")

    """
    try:
        check_is_instance(obj, str, allow_subclass=allow_subclass, name=name)
    except TypeError:
        raise


def check_is_sequence(obj: Sequence, /, *, name: str = 'Object'):
    """Check if an object is an instance of ``Sequence``.

    Parameters
    ----------
    obj : Sequence
        Object to check.

    name : str, default: "Object"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If input is not an instance of ``Sequence``.

    See Also
    --------
    check_is_iterable
    check_is_instance

    Examples
    --------
    Check if an object is a sequence.

    >>> import numpy as np
    >>> from pyvista.core import validate
    >>> validate.check_is_sequence([1, 2, 3])
    >>> validate.check_is_sequence("A")

    """
    try:
        check_is_instance(obj, Sequence, allow_subclass=True, name=name)
    except TypeError:
        raise


def check_is_iterable(obj: Iterable, /, *, name: str = 'Object'):
    """Check if an object is an instance of ``Iterable``.

    Parameters
    ----------
    obj : Iterable
        Iterable object to check.

    name : str, default: "Object"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If input is not an instance of ``Iterable``.

    See Also
    --------
    check_is_sequence
    check_is_instance
    check_is_iterable_of_some_type

    Examples
    --------
    Check if an object is iterable.

    >>> import numpy as np
    >>> from pyvista.core import validate
    >>> validate.check_is_iterable([1, 2, 3])
    >>> validate.check_is_iterable(np.array((4, 5, 6)))

    """
    try:
        check_is_instance(obj, Iterable, allow_subclass=True, name=name)
    except TypeError:
        raise


def check_is_instance(
    obj: Any,
    /,
    classinfo: Union[type, Tuple[type, ...]],
    *,
    allow_subclass: bool = True,
    name: str = 'Object',
):
    """Check if an object is an instance of the given type or types.

    Parameters
    ----------
    obj : Any
        Object to check.

    classinfo : type | tuple[type, ...]
        A type, tuple of types, or a Union of types. Object must be an instance
        of one of the types.

    allow_subclass : bool, default: True
        If ``True``, the object's type must be specified by ``classinfo``
        or any of its subclasses. Otherwise, subclasses are not allowed.

    name : str, default: "Object"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If object is not an instance of any of the given types.

    See Also
    --------
    check_is_type
    check_is_number
    check_is_string
    check_is_iterable
    check_is_sequence

    Examples
    --------
    Check if an object is an instance of ``complex``.

    >>> from pyvista.core import validate
    >>> validate.check_is_instance(1 + 2j, complex)

    Check if an object is an instance of one of several types.

    >>> validate.check_is_instance("eggs", (int, str))

    """
    if not isinstance(name, str):
        raise TypeError(f"Name must be a string, got {type(name)} instead.")

    # Get class info from generics
    if get_origin(classinfo) is Union:
        classinfo = get_args(classinfo)

    # Count num classes
    if isinstance(classinfo, tuple) and all(map(lambda cls: isinstance(cls, type), classinfo)):
        num_classes = len(classinfo)
    else:
        num_classes = 1

    # Check if is instance
    is_instance = isinstance(obj, classinfo)

    # Set flag to raise error if not instance
    is_error = False
    if allow_subclass and not is_instance:
        is_error = True
        if num_classes == 1:
            msg_body = "must be an instance of"
        else:
            msg_body = "must be an instance of any type"

    # Set flag to raise error if not type
    elif not allow_subclass:
        if isinstance(classinfo, tuple):
            if type(obj) not in classinfo:
                is_error = True
                msg_body = "must have one of the following types"
        elif type(obj) is not classinfo:
            is_error = True
            msg_body = "must have type"

    if is_error:
        msg = f"{name} {msg_body} {classinfo}. Got {type(obj)} instead."
        raise TypeError(msg)


def check_is_type(obj: Any, /, classinfo: Union[type, Tuple[type, ...]], *, name: str = 'Object'):
    """Check if an object is one of the given type or types.

    Notes
    -----
    The use of :func:`check_is_instance` is generally preferred as it
    allows subclasses. Use :func:`check_is_type` only for cases where
    exact types are necessary.

    Parameters
    ----------
    obj : Any
        Object to check.

    classinfo : type | tuple[type, ...]
        A type, tuple of types, or a Union of types. Object must be one
        of the types.

    name : str, default: "Object"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If object is not any of the given types.

    See Also
    --------
    check_is_instance

    Examples
    --------
    Check if an object is type ``dict`` or ``set``.

    >>> from pyvista.core import validate
    >>> validate.check_is_type({'spam': "eggs"}, (dict, set))

    """
    try:
        check_is_instance(obj, classinfo, allow_subclass=False, name=name)
    except TypeError:
        raise


def check_is_iterable_of_some_type(
    iterable_obj: Iterable,
    /,
    some_type: Union[type, Tuple[type, ...]],
    *,
    allow_subclass: bool = True,
    name: str = 'Iterable',
):
    """Check if an iterable's items all have a specified type.

    Parameters
    ----------
    iterable_obj : Iterable
        Iterable to check.

    some_type : type | tuple[type, ...]
        Class type(s) to check for. Each element of the sequence must
        have the type or one of the types specified.

    allow_subclass : bool, default: True
        If ``True``, the type of the iterable's items must be any of the
        given types or a subclass thereof. Otherwise, subclasses are not
        allowed.

    name : str, default: "Iterable"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If any of the items in the iterable have an incorrect type.

    See Also
    --------
    check_is_instance
    check_is_iterable
    check_is_iterable_of_strings

    Examples
    --------
    Check if a ``tuple`` only has ``int`` or ``float`` elements.

    >>> from pyvista.core import validate
    >>> validate.check_is_iterable_of_some_type((1, 2, 3.0), (int, float))

    Check if a ``list`` only has ``list`` elements.

    >>> from pyvista.core import validate
    >>> validate.check_is_iterable_of_some_type([[1], [2], [3]], list)

    """
    check_is_iterable(iterable_obj, name=name)
    try:
        # TODO: add bool return to check functions and convert this statement
        # to a generator with all()
        [
            check_is_instance(
                item, some_type, allow_subclass=allow_subclass, name=f"All items of {name}"
            )
            for item in iterable_obj
        ]

    except TypeError:
        raise


def check_is_iterable_of_strings(
    iterable_obj: Iterable, /, *, allow_subclass: bool = True, name: str = 'String Iterable'
):
    """Check if an iterable's items are all strings.

    Parameters
    ----------
    iterable_obj : Iterable
        Iterable of strings to check.

    allow_subclass : bool, default: True
        If ``True``, the type of the iterable's items must be any of the
        given types or a subclass thereof. Otherwise, subclasses are not
        allowed.

    name : str, default: "String Iterable"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If any of the elements have an incorrect type.

    See Also
    --------
    check_is_iterable
    check_is_string
    check_is_string_in_iterable

    Examples
    --------
    Check if a ``tuple`` only has ``str`` elements.

    >>> from pyvista.core import validate
    >>> validate.check_is_iterable_of_strings(("cat", "dog"))

    """
    try:
        check_is_iterable_of_some_type(iterable_obj, str, allow_subclass=allow_subclass, name=name)
    except TypeError:
        raise


def check_is_string_in_iterable(
    string_in: str, /, string_iterable: Iterable, *, name: str = 'String'
):
    """Check if a given string is in an iterable of strings.

    Parameters
    ----------
    string_in : str
        String to check.

    string_iterable : Iterable
        Iterable containing only strings.

    name : str, default: "String"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If the string is not in the iterable.

    See Also
    --------
    check_is_iterable
    check_is_string
    check_is_iterable_of_strings

    Examples
    --------
    Check if ``"A"`` is in a list of strings.

    >>> from pyvista.core import validate
    >>> validate.check_is_string_in_iterable("A", ["A", "B", "C"])

    """
    check_is_string(string_in, name=name)
    check_is_iterable_of_strings(string_iterable)
    if string_in not in string_iterable:
        raise ValueError(
            f"{name} '{string_in}' is not in the iterable. "
            f"{name} must be one of: \n\t" + str(string_iterable)
        )


def check_has_length(
    arr: Union[npt.ArrayLike, Sized],
    /,
    *,
    exact_length: Union[int, IntVector, None] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    must_be_1d: bool = False,
    allow_scalar: bool = False,
    name: str = "Array",
):
    """Check if the length of an array meets specific requirements.

    Notes
    -----
    By default, this function operates on multidimensional arrays,
    where ``len(arr)`` may differ from the number of elements in the
    array. For one-dimensional cases (where ``len(arr) == arr.size``),
    set ``must_be_1D=True``.

    Parameters
    ----------
    arr : numpy.typing.ArrayLike
        Array to check.

    exact_length : int | IntVector, optional
        Check if the array has the given length. If multiple
        numbers are given, the array's length must match one of the
        numbers.

    min_length : int, optional
        Check if the array has this length or greater.

    max_length : int, optional
        Check if the array has this length or less.

    must_be_1d : bool, default: False
        If ``True``, check if the shape of the array is one-dimensional,
        i.e. that the array's shape is ``(1,)``.

    allow_scalar : bool, default: False
        If ``True``, a scalar input will be reshaped to have a length
        of 1. Otherwise, the check will fail since a scalar does not
        have a length.

    name : str, default: "Array"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    ValueError
        If the array's length is outside the specified range.

    See Also
    --------
    check_has_shape

    Examples
    --------
    Check if an array has a length of 2 or 3.

    >>> from pyvista.core import validate
    >>> validate.check_has_length([1, 2], exact_length=[2, 3])

    Check if an array has a minimum length of 3.

    >>> validate.check_has_length((1, 2, 3), min_length=3)

    Check if a multidimensional array has a maximum length of 2.

    >>> validate.check_has_length([[1, 2, 3], [4, 5, 6]], max_length=2)

    """
    if allow_scalar:
        # Reshape to 1D
        if isinstance(arr, Number):
            arr = np.array([arr])
        elif isinstance(arr, np.ndarray) and arr.ndim == 0:
            arr = arr.reshape((1,))

    check_is_instance(arr, (Sequence, np.ndarray), name=name)

    if must_be_1d:
        check_has_shape(arr, shape=(-1))  # type: ignore[arg-type]

    arr_len = len(cast(Sized, arr))

    if exact_length is not None:
        exact_length = cast(np.ndarray, cast_to_ndarray(exact_length))
        check_is_integerlike(exact_length, name="'exact_length'")
        if arr_len not in exact_length:
            raise ValueError(
                f"{name} must have a length equal to any of: {exact_length}. "
                f"Got length {arr_len} instead."
            )

    # Validate min/max length
    if min_length is not None:
        min_length = cast_to_ndarray(min_length)  # type: ignore
        check_is_scalar(min_length, name="Min length")
        check_is_real(min_length, name="Min length")
    if max_length is not None:
        max_length = cast_to_ndarray(max_length)  # type: ignore
        check_is_scalar(max_length, name="Max length")
        check_is_real(max_length, name="Max length")
    if min_length is not None and max_length is not None:
        check_is_sorted((min_length, max_length), name="Range")

    if min_length is not None:
        if arr_len < min_length:
            raise ValueError(
                f"{name} must have a minimum length of {min_length}. "
                f"Got length {arr_len} instead."
            )
    if max_length is not None:
        if arr_len > max_length:
            raise ValueError(
                f"{name} must have a maximum length of {max_length}. "
                f"Got length {arr_len} instead."
            )


def _validate_shape_value(shape: ShapeLike) -> Shape:
    """Validate shape-like input and return its tuple representation."""
    if shape is None:
        # `None` is used to mean `any shape is allowed` by the array
        #  validation methods, so raise an error here.
        #  Also, setting `None` as a shape is deprecated by NumPy.
        raise TypeError("`None` is not a valid shape. Use `()` instead.")

    # Return early for common inputs
    if shape == ():
        return cast(Shape, shape)
    elif shape in [(-1,), (1,), (3,), (2,), (1, 3), (-1, 3)]:
        return cast(Shape, shape)

    def _is_valid_dim(d):
        return isinstance(d, int) and d >= -1

    if _is_valid_dim(shape):
        return (cast(int, shape),)
    if isinstance(shape, tuple) and all(map(_is_valid_dim, shape)):
        return cast(Shape, shape)

    # Input is not valid at this point. Use checks to raise an
    # appropriate error
    check_is_instance(shape, (int, tuple), name='Shape')
    if isinstance(shape, int):
        shape = (shape,)
    else:
        check_is_iterable_of_some_type(shape, int, name='Shape')
    check_is_greater_than(shape, -1, name="Shape", strict=False)
    raise RuntimeError("This line should not be reachable.")  # pragma: no cover


def check_is_scalar(
    scalar: Union[float, int, complex, Number, np.number, np.ndarray],
    /,
    *,
    must_be_real: bool = True,
    name: str = "Scalar",
):
    """Check if an object is a scalar number.

    By default, the number must be real, or a 0-dimensional :class:`numpy.ndarray`
    of a real number. Optionally, the scalar can also be a complex

    This check is similar to :func:`check_is_number` but also allows 0-dimensional
    arrays.

    Notes
    -----
    Values such as ``infinity`` and ``NaN`` are valid scalars and will not
    raise an error. Use :func:`check_is_finite` to check for finite values.

    Parameters
    ----------
    scalar : float | int | complex | Number | numpy.number | numpy.ndarray
        Number or 0-dimensional numeric array.

    must_be_real : bool, default: True
        If ``True``, the scalar must be a real number, i.e. an integer or
        floating type. Set to ``False`` to allow complex numbers.

    name : str, default: "Scalar"
        Variable name to use in the error messages if any are raised.

    Raises
    ------
    TypeError
        If input is not a number or a 0-dimensional number array.

    See Also
    --------
    check_is_number
        Similar function which does not allow 0-dimensional ndarrays.
    check_is_numeric
        Similar function for any dimensional array of numbers.
    check_is_real
        Similar function for any dimensional array of real numbers.
    check_is_finite

    Examples
    --------
    Check if an object is scalar.

    >>> import numpy as np
    >>> from pyvista.core import validate
    >>> validate.check_is_scalar(0.0)
    >>> validate.check_is_scalar(np.array(1))
    >>> validate.check_is_scalar(np.array(1 + 2j), must_be_real=False)

    """
    try:
        if isinstance(scalar, np.ndarray):
            # TODO: check_has_ndim(scalar, 0)
            if scalar.ndim > 0:
                raise ValueError(
                    f"{name} must be a 0-dimensional array, got `ndim={scalar.ndim}` instead."
                )
            check_is_real(scalar, name=name) if must_be_real else check_is_numeric(
                scalar, name=name
            )
        else:
            check_is_number(scalar, must_be_real=must_be_real)
    except TypeError:
        raise
