#![deny(clippy::pedantic)]
#![deny(clippy::restriction)]
#![allow(clippy::arithmetic_side_effects)]
#![allow(clippy::blanket_clippy_restriction_lints)]
#![allow(clippy::exhaustive_enums)]
#![allow(clippy::float_arithmetic)]
#![allow(clippy::implicit_return)]
#![allow(clippy::min_ident_chars)]
#![allow(clippy::missing_docs_in_private_items)]

use core::cmp;
use core::fmt::{
    Binary, Debug, Display, Formatter, LowerExp, LowerHex, Octal, Pointer, Result as FmtResult,
    UpperExp, UpperHex,
};
use core::ops::{Add, BitAnd, BitOr, BitXor, Div, Mul, Neg, Not, Rem, Shl, Shr, Sub};
use num_traits::Pow;

use crate::base::Base;
use crate::natural::{Maybe, Natural};
use crate::negative::Negative;
use crate::number::Number;
use crate::traits::NumberBase;
use crate::utils::fmt_ptr;

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum Part {
    Base(Base),
    Natural(Natural),
}

#[allow(clippy::missing_trait_methods)]
impl PartialEq<u64> for Part {
    #[inline]
    fn eq(&self, other: &u64) -> bool {
        match self.clone() {
            Self::Base(a) => a == *other,
            Self::Natural(a) => a == *other,
        }
    }
}

impl From<u64> for Part {
    #[inline]
    fn from(i: u64) -> Self {
        Self::Base(Base::new(i))
    }
}
impl From<Base> for Part {
    #[inline]
    fn from(i: Base) -> Self {
        Self::Base(i)
    }
}
impl From<Natural> for Part {
    #[inline]
    fn from(i: Natural) -> Self {
        match i.reduce() {
            Maybe::Base(v) => Self::Base(v),
            Maybe::Natural(v) => Self::Natural(v),
        }
    }
}
impl TryFrom<Number> for Part {
    type Error = &'static str;
    #[inline]
    fn try_from(i: Number) -> Result<Self, Self::Error> {
        match i {
            Number::Base(v) => Ok(Self::Base(v)),
            Number::Natural(v) => Ok(Self::Natural(v)),
            Number::Rational(_)
            | Number::Negative(_)
            | Number::Imag(_)
            | Number::Complex(_)
            | Number::NaN => Err("invalid number type"),
        }
    }
}

impl From<Part> for Number {
    #[inline]
    fn from(part: Part) -> Self {
        match part {
            Part::Base(a) => Self::from(a),
            Part::Natural(a) => Self::from(a),
        }
    }
}

#[allow(clippy::integer_division)]
#[allow(clippy::missing_trait_methods)]
impl num_traits::ToPrimitive for Part {
    #[inline]
    fn to_i64(&self) -> Option<i64> {
        match self.clone() {
            Self::Base(a) => a.to_i64(),
            Self::Natural(a) => a.to_i64(),
        }
    }
    #[inline]
    fn to_u64(&self) -> Option<u64> {
        match self.clone() {
            Self::Base(a) => a.to_u64(),
            Self::Natural(a) => a.to_u64(),
        }
    }
    #[inline]
    fn to_f64(&self) -> Option<f64> {
        match self.clone() {
            Self::Base(a) => a.to_f64(),
            Self::Natural(a) => a.to_f64(),
        }
    }
}

impl Mul for Part {
    type Output = Number;
    #[inline]
    fn mul(self, other: Self) -> Self::Output {
        match (self, other) {
            (Self::Base(a), Self::Base(b)) => a * b,
            (Self::Base(a), Self::Natural(b)) | (Self::Natural(b), Self::Base(a)) => b * a.into(),
            (Self::Natural(a), Self::Natural(b)) => a * b,
        }
    }
}

impl Part {
    #[inline]
    #[must_use]
    fn div_floor(self, other: Self) -> Number {
        match (self, other) {
            (Self::Base(a), Self::Base(b)) => a.div_floor(b),
            (Self::Base(a), Self::Natural(b)) => Natural::from(a).div_floor(b),
            (Self::Natural(a), Self::Base(b)) => a.div_floor(b.into()),
            (Self::Natural(a), Self::Natural(b)) => a.div_floor(b),
        }
    }
    #[inline]
    #[must_use]
    fn gcd(self, other: Self) -> Number {
        match (self, other) {
            (Self::Base(a), Self::Base(b)) => a.gcd(b),
            (Self::Base(a), Self::Natural(b)) | (Self::Natural(b), Self::Base(a)) => {
                b.gcd(a.into())
            }
            (Self::Natural(a), Self::Natural(b)) => a.gcd(b),
        }
    }
}

impl Display for Part {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter) -> FmtResult {
        match self.clone() {
            Self::Base(n) => write!(formatter, "{n}"),
            Self::Natural(n) => write!(formatter, "{n}"),
        }
    }
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub struct Rational {
    numerator: Part,
    denominator: Part,
}

#[allow(clippy::missing_trait_methods)]
impl PartialEq<u64> for Rational {
    #[inline]
    fn eq(&self, _other: &u64) -> bool {
        false
    }
}

#[allow(clippy::missing_trait_methods)]
impl PartialOrd<u64> for Rational {
    #[inline]
    fn partial_cmp(&self, other: &u64) -> Option<cmp::Ordering> {
        Some(
            Number::from(self.numerator.clone()).cmp(&(self.denominator.clone() * (*other).into())),
        )
    }
}
#[allow(clippy::missing_trait_methods)]
impl PartialOrd<Rational> for Rational {
    #[inline]
    fn partial_cmp(&self, other: &Self) -> Option<cmp::Ordering> {
        Some(self.cmp(other))
    }
}

#[allow(clippy::missing_trait_methods)]
impl Ord for Rational {
    #[inline]
    fn cmp(&self, other: &Self) -> cmp::Ordering {
        (self.numerator.clone() * other.denominator.clone())
            .cmp(&(other.numerator.clone() * self.denominator.clone()))
    }
}

impl<T: Into<Part>> From<T> for Rational {
    #[inline]
    fn from(i: T) -> Self {
        Self {
            numerator: i.into(),
            denominator: 1.into(),
        }
    }
}
impl<T: Into<Part>, U: Into<Part>> From<(T, U)> for Rational {
    #[inline]
    fn from(i: (T, U)) -> Self {
        Self {
            numerator: i.0.into(),
            denominator: i.1.into(),
        }
    }
}

impl Rational {
    #[inline]
    #[must_use]
    pub fn reduce(self) -> Number {
        if self.denominator == 0 || self.numerator == 1 {
            Number::Rational(self)
        } else if self.numerator == 0 {
            0.into()
        } else if self.denominator == 1 {
            self.numerator.into()
        } else {
            let gcd = self.numerator.clone().gcd(self.denominator.clone());
            if gcd == 1 {
                Number::Rational(self)
            } else if gcd == Number::from(self.denominator.clone()) {
                Number::from(self.numerator).div_floor(gcd)
            } else {
                Part::try_from(Number::from(self.numerator).div_floor(gcd.clone()))
                    .and_then(|n| {
                        Part::try_from(Number::from(self.denominator).div_floor(gcd))
                            .map(|d| (n, d))
                    })
                    .map(Self::from)
                    .map_or_else(|_| Number::NaN, Number::Rational)
            }
        }
    }
}

#[allow(clippy::integer_division)]
#[allow(clippy::missing_trait_methods)]
impl num_traits::ToPrimitive for Rational {
    #[inline]
    fn to_i64(&self) -> Option<i64> {
        self.numerator
            .to_i64()
            .and_then(|x| self.denominator.to_i64().map(|y| x / y))
    }
    #[inline]
    fn to_u64(&self) -> Option<u64> {
        self.numerator
            .to_u64()
            .and_then(|x| self.denominator.to_u64().map(|y| x / y))
    }
    #[inline]
    fn to_f64(&self) -> Option<f64> {
        self.numerator
            .to_f64()
            .and_then(|x| self.denominator.to_f64().map(|y| x / y))
    }
}

impl Binary for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        write!(formatter, "{}/{}", self.numerator, self.denominator)
    }
}

impl Display for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        write!(formatter, "{}/{}", self.numerator, self.denominator)
    }
}

impl LowerExp for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        write!(formatter, "{}/{}", self.numerator, self.denominator)
    }
}

impl LowerHex for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        write!(formatter, "{}/{}", self.numerator, self.denominator)
    }
}

impl Octal for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        write!(formatter, "{}/{}", self.numerator, self.denominator)
    }
}

impl Pointer for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        fmt_ptr(self, formatter)
    }
}

impl UpperExp for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        write!(formatter, "{}/{}", self.numerator, self.denominator)
    }
}

impl UpperHex for Rational {
    #[inline]
    fn fmt(&self, formatter: &mut Formatter<'_>) -> FmtResult {
        write!(formatter, "{}/{}", self.numerator, self.denominator)
    }
}

impl Add for Rational {
    type Output = Number;
    #[inline]
    fn add(self, other: Self) -> Self::Output {
        ((self.numerator * other.denominator.clone())
            + (self.denominator.clone() * other.numerator))
            / (self.denominator * other.denominator)
    }
}

impl BitAnd for Rational {
    type Output = Number;
    #[inline]
    fn bitand(self, _other: Self) -> Self::Output {
        Number::NaN
    }
}

impl BitOr for Rational {
    type Output = Number;
    #[inline]
    fn bitor(self, _other: Self) -> Self::Output {
        Number::NaN
    }
}

impl BitXor for Rational {
    type Output = Number;
    #[inline]
    fn bitxor(self, _other: Self) -> Self::Output {
        Number::NaN
    }
}

impl Div for Rational {
    type Output = Number;
    #[inline]
    fn div(self, other: Self) -> Self::Output {
        (self.numerator * other.denominator) / (self.denominator * other.numerator)
    }
}

impl Mul for Rational {
    type Output = Number;
    #[inline]
    fn mul(self, other: Self) -> Self::Output {
        (self.numerator * other.numerator) / (self.denominator * other.denominator)
    }
}

impl Neg for Rational {
    type Output = Number;
    #[inline]
    fn neg(self) -> Self::Output {
        Negative::Rational(self).into()
    }
}

impl Not for Rational {
    type Output = Number;
    #[inline]
    fn not(self) -> Self::Output {
        Number::NaN
    }
}

impl Pow<Rational> for Rational {
    type Output = Number;
    #[inline]
    fn pow(self, _other: Self) -> Number {
        Number::NaN
    }
}

impl Rem for Rational {
    type Output = Number;
    #[inline]
    fn rem(self, other: Self) -> Self::Output {
        let left: Number = self.into();
        let right: Number = other.into();
        left.clone() - (left.div_floor(right.clone()) * right)
    }
}

impl Shl for Rational {
    type Output = Number;
    #[inline]
    fn shl(self, _other: Self) -> Self::Output {
        Number::NaN
    }
}

impl Shr for Rational {
    type Output = Number;
    #[inline]
    fn shr(self, _other: Self) -> Self::Output {
        Number::NaN
    }
}

impl Sub for Rational {
    type Output = Number;
    #[inline]
    fn sub(self, other: Self) -> Self::Output {
        ((self.numerator * other.denominator.clone())
            - (self.denominator.clone() * other.numerator))
            / (self.denominator * other.denominator)
    }
}

#[allow(clippy::missing_trait_methods)]
impl NumberBase for Rational {
    #[inline]
    #[must_use]
    fn div_floor(self, other: Self) -> Number {
        match self / other {
            Number::Rational(r1) => match r1.reduce() {
                Number::Rational(r2) => r2.numerator.div_floor(r2.denominator),
                n @ (Number::Base(_)
                | Number::Natural(_)
                | Number::Negative(_)
                | Number::Imag(_)
                | Number::Complex(_)
                | Number::NaN) => n,
            },
            n @ (Number::Base(_)
            | Number::Natural(_)
            | Number::Negative(_)
            | Number::Imag(_)
            | Number::Complex(_)
            | Number::NaN) => n,
        }
    }
}
