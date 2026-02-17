from datetime import date, timedelta

def get_start_weekday_of_month(year, month):
    """
    월의 시작 요일을 가져옴(월=0 ~ 일=6)

    >>> get_start_weekday_of_month(2024, 12)
    6
    >>> get_start_weekday_of_month(2025, 2)
    5
    """
    result = date(year, month, 1)   # (1)
    return result.weekday() # (2)

def get_last_day_of_month(year, month):
    """
    월의 마지막 날짜를 가져옴

    >>> get_last_day_of_month(2024, 2)
    29
    >>> get_last_day_of_month(2025, 2)
    28
    >>> get_last_day_of_month(2024, 4)
    30
    >>> get_last_day_of_month(2024, 12)
    31
    """
    if month == 12: # (1)
        next_month = date(year+1, 1, 1)
    else:
        next_month = date(year, month+1, 1)

    result = next_month - timedelta(days=1) # (2)
    return result.day   #(3)

def get_range_days_of_month(year, month):
    # 월의 시작 요일을 가져옴(월=0 ~ 일=6)
    start_weekday = get_start_weekday_of_month(year,month)

    # 월의 마지막 날짜를 가져옴
    last_day = get_last_day_of_month(year, month)

    # 월=0을 월=1로 변환(일=0으로 만들기 위해)
    start_weekday = (start_weekday + 1) % 7

    # 결과 리스트 생성
    result = [0] * start_weekday    # 시작 요일 전까지 0으로 채움

    # # 1일부터 마지막날까지 추가
    # for day in range(1, last_day+1):
    #     result.append(day)

    return result + list(range(1, last_day+1))