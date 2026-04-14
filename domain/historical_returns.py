"""S&P 500 historical annual total returns (1928-2024)."""

# Annual total returns (including dividends) sourced from public market data
SP500_ANNUAL_RETURNS: dict[int, float] = {
    1928: 0.4381, 1929: -0.0830, 1930: -0.2512, 1931: -0.4384, 1932: -0.0819,
    1933: 0.5399, 1934: -0.0119, 1935: 0.4767, 1936: 0.3344, 1937: -0.3506,
    1938: 0.3112, 1939: -0.0041, 1940: -0.0978, 1941: -0.1159, 1942: 0.2034,
    1943: 0.2590, 1944: 0.1975, 1945: 0.3644, 1946: -0.0807, 1947: 0.0371,
    1948: 0.0548, 1949: 0.1879, 1950: 0.3155, 1951: 0.2440, 1952: 0.1837,
    1953: -0.0099, 1954: 0.5256, 1955: 0.3156, 1956: 0.0656, 1957: -0.1078,
    1958: 0.4336, 1959: 0.1195, 1960: 0.0047, 1961: 0.2669, 1962: -0.0873,
    1963: 0.2280, 1964: 0.1676, 1965: 0.1242, 1966: -0.1010, 1967: 0.2398,
    1968: 0.1106, 1969: -0.0850, 1970: 0.0404, 1971: 0.1431, 1972: 0.1903,
    1973: -0.1466, 1974: -0.2647, 1975: 0.3720, 1976: 0.2344, 1977: -0.0718,
    1978: 0.0656, 1979: 0.1844, 1980: 0.3242, 1981: -0.0491, 1982: 0.2141,
    1983: 0.2234, 1984: 0.0627, 1985: 0.3216, 1986: 0.1547, 1987: 0.0502,
    1988: 0.1681, 1989: 0.3169, 1990: -0.0317, 1991: 0.3058, 1992: 0.0744,
    1993: 0.0997, 1994: 0.0133, 1995: 0.3758, 1996: 0.2296, 1997: 0.3310,
    1998: 0.2858, 1999: 0.1954, 2000: -0.0910, 2001: -0.1189, 2002: -0.2202,
    2003: 0.2868, 2004: 0.1088, 2005: 0.0488, 2006: 0.1576, 2007: 0.0504,
    2008: -0.3700, 2009: 0.2646, 2010: 0.1288, 2011: 0.0200, 2012: 0.1600,
    2013: 0.2968, 2014: 0.1342, 2015: 0.0138, 2016: 0.0996, 2017: 0.2104,
    2018: -0.0606, 2019: 0.2920, 2020: 0.1238, 2021: 0.2869, 2022: -0.1820,
    2023: 0.2426, 2024: 0.2523,
}

HISTORICAL_START_YEAR = 1928
HISTORICAL_END_YEAR = 2024


def get_historical_rate_sequence(start_year: int, num_years: int) -> list[float]:
    """
    Generate sequence of annual return rates from S&P 500 historical data.

    Wraps around if simulation exceeds available data (e.g., 10-year simulation
    starting in 2020 uses 2020-2024 then wraps to 1928-1933).

    Args:
        start_year: Calendar year to begin sequence (must be 1928-2024)
        num_years: Number of years to generate

    Returns:
        List of annual return rates (floats)

    Raises:
        ValueError: If start_year not in available data (1928-2024)
    """
    if start_year not in SP500_ANNUAL_RETURNS:
        raise ValueError(
            f"Historical data available for {HISTORICAL_START_YEAR}-{HISTORICAL_END_YEAR}. "
            f"Got start_year={start_year}"
        )

    rates = []
    current_year = start_year

    for _ in range(num_years):
        # Wrap around: when past 2024, jump back to 1928
        if current_year > HISTORICAL_END_YEAR:
            current_year = HISTORICAL_START_YEAR + (current_year - HISTORICAL_END_YEAR - 1)

        rates.append(SP500_ANNUAL_RETURNS[current_year])
        current_year += 1

    return rates
