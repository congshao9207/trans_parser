# -*- coding: utf-8 -*-
# @Project : trans-parser
# @IDE : PyCharm
# @Author : lixiaobo
# @Date : 12/13/24 4:44 PM
# @Version : 1.0
# @Description :
import time

import pytest

from componentt.perf_stats import PerfStats

ps = PerfStats()


@pytest.fixture
def perf_stats():
    start = time.time() * 1000
    yield ps
    cost_mill = time.time() * 1000 - start
    ps.add_stats(int(cost_mill))
