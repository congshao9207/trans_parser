# -*- coding: utf-8 -*-
# @Project : trans-parser
# @IDE : PyCharm
# @Author : lixiaobo
# @Date : 12/12/24 2:56 PM
# @Version : 1.0
# @Description :
import logging
import re

from regex import regex

from componentt.preparse_test import pre_parse

logging.getLogger('pdfminer').setLevel(logging.ERROR)


def preparse_assert(func):
    def wrapper(*args, **kwargs):
        result, predicate = func(*args, **kwargs)
        assert result['bank_name'] == predicate[0]
        assert result['bank_account'] == predicate[1]
        assert result['user_name'] == predicate[2]

    return wrapper


@preparse_assert
def test_blank_char():
    path = '../resource/预解析优化文件/01 账号存在空格/44406c15-7184-46a5-8c29-517361d01d4d.pdf'
    return pre_parse(path), ['', '6214651046331525', '万兵']


@preparse_assert
def test_parse_account_no():
    path = '../resource/预解析优化文件/06 账号未正常识别/14b133fc-9c55-401f-8d15-9e021d343026.pdf'
    return pre_parse(path), ['成都农村商业银行股份有限公司', '6230880006043889756', '刘韬']


@preparse_assert
def test_parse_account_no1():
    path = '../resource/预解析优化文件/05 银行未正常识别/a3fa3f8b-bb1f-4e51-9d26-08da8cde62fa.pdf'
    return pre_parse(path), ['金瑞支行', '810000345412000001', '湖南紫景园林景观工程有限公司']


@preparse_assert
def test_parse_account_no2():
    path = '../resource/预解析优化文件/05 银行未正常识别/b16f867d-85bc-4ed3-a8f0-e7acfe48307f.pdf'
    return pre_parse(path), ['湖北大冶泰隆村镇银行还地桥支行', '6235350010648031', '刘可']


@preparse_assert
def test_parse_account_name1():
    path = '../resource/预解析优化文件/04 账户名称识别错误/534936b6-23d6-4ce7-849d-70bef9a336e8.pdf'
    return pre_parse(path), ['', '8111001013000776200', '成都恒美云美容有限公司']


@preparse_assert
def test_parse_account_name2():
    path = '../resource/预解析优化文件/04 账户名称识别错误/f38aac48-1e9e-4fb5-b7cf-d67957048922.pdf'
    return pre_parse(path), ['上海农商银行', '50131000347900720', '上海浦鑫水电安装有限公司']


@preparse_assert
def test_multi_line1():
    path = '../resource/预解析优化文件/02 账户名称多行显示/5c46db94-b4e1-45eb-915d-376bc5d15319.pdf'
    return pre_parse(path), ['', '10655900***0791', '圾清理有限']


@preparse_assert
def test_multi_line2():
    path = '../resource/预解析优化文件/02 账户名称多行显示/43d10dc7-b133-4e34-a243-a24a46f6f9aa.pdf'
    return pre_parse(path), ['', '10655900***0791', '圾清理有限']


@preparse_assert
def test_from_content():
    path = '../resource/预解析优化文件/03 从内容中识别信息/额度17万版本.xlsx'
    return pre_parse(path), ['', '801040011010100070398', '丁丽']


@preparse_assert
def test_parse_xls():
    path = '../resource/预解析优化文件/07 xls文件/2023.11-2024.11企业银行人民币账户.xls'
    return pre_parse(path), ['', '727701837327001', '']


@preparse_assert
def test_parse_wepay():
    path = '../resource/预解析优化文件/1628670460589_微信流水1.pdf'
    return pre_parse(path), ['微信支付', 'tz13668075132', '马洪法']


@preparse_assert
def test_parse_alipay():
    path = '../resource/预解析优化文件/1628670469318_支付宝流水.pdf'
    return pre_parse(path), ['支付宝', '15201768010', '黄锦文']


@preparse_assert
def test_parse_alipay1():
    path = '../resource/预解析优化文件/支付宝流水示例.pdf'
    return pre_parse(path), ['支付宝', '17521382576', '韦平安']


@preparse_assert
def test_parse_1():
    path = '../resource/预解析优化文件/fc8815b4-dcf7-40ba-baae-21f696dd40b7.pdf'
    return pre_parse(path), ['长沙分行韶山路支行', '731907934510602', '湖南金易建设工程有限公司']


@preparse_assert
def test_parse_2():
    path = '../resource/预解析优化文件/dd7931f6-87e1-4d08-98c8-b499bb551eb3.pdf'
    return pre_parse(path), ['', '8111601010700495232', '长沙伟诺汽车制造有限公司']


@preparse_assert
def test_parse_3():
    path = '../resource/预解析优化文件/706f9990-4ae5-4f88-898e-b1c5baff544f.pdf'
    return pre_parse(path), ['中国民生银行股份有限公司', '6226222702325429', '毕兆松']


@preparse_assert
def test_parse_4():
    path = '../resource/预解析优化文件/0b43a08a-d4ae-4fa1-8f4d-13932733a43c.pdf'
    return pre_parse(path), ['支付宝', '269213978@qq.com', '徐志强']


@preparse_assert
def test_parse_5():
    path = '../resource/预解析优化文件/0fde7930-9929-4f81-8aba-31f533f4f466.pdf'
    return pre_parse(path), ['微信支付', 'wxid_184760myfkjr22', '曾海燕']


@preparse_assert
def test_parse_6():
    path = '../resource/预解析优化文件/4.pdf'
    return pre_parse(path), ['支付宝', '18720352968@qq.com', '林鹏']


@preparse_assert
def test_parse_7():
    path = '../resource/预解析优化文件/5f3ecda2-c0e8-4089-98c1-e37e388b75d8.pdf'
    return pre_parse(path), ['支付宝', 'sitongyang@qq.com', '佀同洋']


@preparse_assert
def test_parse_8():
    path = '../resource/预解析优化文件/nonghang.pdf'
    return pre_parse(path), ['中国农业银⾏', '6230520240016948572', '曲章哲']


@preparse_assert
def test_parse_9():
    path = '../resource/预解析优化文件/1ab98f2c-a750-4f7f-bbdc-f27b6b92dbff.pdf'
    return pre_parse(path), ['微信支付', 'shao_lao_shi', '邵健健']


@preparse_assert
def test_parse_10_exception():
    path = '../resource/预解析优化文件/batch01/用户+账号+银行名称 解析异常.pdf'
    return pre_parse(path), ['中国光大银行', '52140188000063057', '安徽叶记生鲜食品配送有限公司']


@preparse_assert
def test_parse_11_exception():
    path = '../resource/预解析优化文件/batch01/用户名 解析异常.pdf'
    return pre_parse(path), ['苏州农村商业银行', '6231****3398', '徐成']


@preparse_assert
def test_parse_12_exception():
    path = '../resource/预解析优化文件/batch01/账号 解析异常 2.pdf'
    return pre_parse(path), ['徽商银行', '1761601021000188302', '安徽中辰保安服务有限公司']


@preparse_assert
def test_parse_13_exception():
    path = '../resource/预解析优化文件/batch01/账号+用户名  解析异常.pdf'
    return pre_parse(path), ['', '535904270210111', '山东乐塔生物科技有限公司']


@preparse_assert
def test_parse_14_exception():
    path = '../resource/预解析优化文件/batch01/账号+用户名解析异常.pdf'
    return pre_parse(path), ['交通银行', '6222601010015681055', '姜吉俊']


@preparse_assert
def test_parse_15_exception():
    path = '../resource/预解析优化文件/batch01/银行名称 解析异常2.pdf'
    return pre_parse(path), ['长沙分行韶山路支行', '731907934510602', '湖南金易建设工程有限公司']


@preparse_assert
def test_parse_16_exception():
    path = '../resource/预解析优化文件/batch01/银行名称+账号 解析异常.pdf'
    return pre_parse(path), ['中国民生银行股份有限公司', '6226222702325429', '毕兆松']


@preparse_assert
def test_parse_17_exception():
    path = '../resource/problems/c09f108a-d916-4d9a-ac09-87f4881cb0b9.pdf'
    return pre_parse(path), ['', '6212583013998386', '刁利祥']


@preparse_assert
def test_problem1():
    path = '../resource/problems/3b7b87ab-f963-46c5-b284-6d32886357de.pdf'
    return pre_parse(path), ['', '6230****4576', '姜爱华']


@preparse_assert
def test_problem3():
    path = '../resource/problems/6ec64018-4a7a-41ae-89fb-59e38f993459.pdf'
    return pre_parse(path), ['', '44-650101040027012', '深圳宏峰建设有限公司']


@preparse_assert
def test_problem4():
    path = '../resource/problems/6f199149-c247-4c43-92c7-4e74d31bf002.pdf'
    return pre_parse(path), ['', '6217710500993720', '朱建辉']


@preparse_assert
def test_problem7():
    path = '../resource/problems/38bf0b85-eb60-4792-b9bc-bb9cc75f8db7.pdf'
    return pre_parse(path), ['重庆三峡银行', '6217550201264330', '聂小周']


@preparse_assert
def test_problem8():
    path = '../resource/problems/40e25b31-c5fe-4118-961c-21ed7b2ad123.pdf'
    return pre_parse(path), ['中国建设银行', '', '上海悦康建筑安装工程有限公司']


@preparse_assert
def test_problem9():
    path = '../resource/problems/85b5fe0d-37ba-4982-9094-28169aa6f218.pdf'
    return pre_parse(path), ['北京银行', '20000034936600019872807', '北京市瀛源建设工程有限公司']


@preparse_assert
def test_problem10():
    path = '../resource/problems/86b3cfee-c212-4526-bebe-e663c5d0afb0.pdf'
    return pre_parse(path), ['', '03-348700040019221', '上海景宏商务酒店有限公司']


@preparse_assert
def test_problem11():
    path = '../resource/problems/367f8e74-8c6e-4624-8e0e-03f6cbf25edc.pdf'
    return pre_parse(path), ['', '31-620501040008630', '重庆旭唐建设工程有限公司']


@preparse_assert
def test_problem12():
    path = '../resource/problems/8163f164-35ee-48d2-b10f-bff38c467c94.pdf'
    return pre_parse(path), ['重庆三峡银行', '6217550201264330', '聂小周']


@preparse_assert
def test_problem13():
    path = '../resource/problems/25160df7-9a5f-40fc-9ad4-ce395ef69843.pdf'
    return pre_parse(path), ['', '', '']
    # 扫描件


@preparse_assert
def test_problem14():
    path = '../resource/problems/50863d91-c148-4942-ae17-4ba66615b4e6.pdf'
    return pre_parse(path), ['深圳农商银行', '600', '黄子华']


@preparse_assert
def test_problem15():
    path = '../resource/problems/105093bd-9a85-45ba-922e-f767f5b54d25.pdf'
    return pre_parse(path), ['', '03-481300040034764', '上海隆渊建设集团有限公司']


@preparse_assert
def test_problem18():
    path = '../resource/problems/25885922-e4ad-4fa9-ba56-9041d46b9c4c.pdf'
    return pre_parse(path), ['', '', '']
    # 无数据


@preparse_assert
def test_problem19():
    path = '../resource/problems/a4b88a00-3c6e-48c4-89fd-8ce289b74ebd.pdf'
    return pre_parse(path), ['', '583670645800015', '上海赛峰建筑装饰工程有限公司']


@preparse_assert
def test_problem20():
    path = '../resource/problems/b3de50f1-0f07-4297-acf9-9b3a09742a1f.pdf'
    return pre_parse(path), ['兴业银行', '622908406277439918', '洪文斌']


@preparse_assert
def test_problem21():
    path = '../resource/problems/c7f127c7-dd65-4186-b896-10141ab37350.pdf'
    return pre_parse(path), ['四川天府银行', '2000155143000014', '']


@preparse_assert
def test_problem23():
    path = '../resource/problems/d048aa1c-c5a6-48e3-ba4a-bc70ee2ecf8d.pdf'
    return pre_parse(path), ['江苏海门农村商业银行', '6230****4693', '李亮华']


@preparse_assert
def test_problem24():
    path = '../resource/problems/d136ab2e-1c78-491a-9cd3-e836dad936a8.pdf'
    return pre_parse(path), ['四川天府银行', '2000155143000014', '']


@preparse_assert
def test_problem25():
    path = '../resource/problems/e6874ee6-de83-4c87-8436-e1ef14275187.pdf'
    return pre_parse(path), ['兴业银行', '622908406277439918', '洪文斌']


@preparse_assert
def test_problem26():
    path = '../resource/problems/f942e8bb-d6e1-4e89-a5ca-f7c0bb54c489.pdf'
    return pre_parse(path), ['兴业银行', '622908406277439918', '洪文斌']


@preparse_assert
def test_problem27():
    path = '../resource/problems/fa92be2f-ece8-42a8-87d7-534cd0120320.pdf'
    return pre_parse(path), ['青田农商银行海口支行', '6210580999001335082', '殷军平']


@preparse_assert
def test_batch02_1():
    path = '../resource/预解析优化文件/batch02/劳务徽行1-6月.xls'
    return pre_parse(path), ['', '1021001021000946587', '安徽皖云建筑劳务有限公司']


@preparse_assert
def test_batch02_2():
    path = '../resource/预解析优化文件/batch02/1(2).xls'
    return pre_parse(path), ['', '43050163730800000429', '湘潭市美利冷食有限公司']


@preparse_assert
def test_batch02_3():
    path = '../resource/预解析优化文件/batch02/1651195120524_蜀嘉流水.pdf'
    return pre_parse(path), ['', '650592944200015', '重庆蜀嘉物流有限公司']


@preparse_assert
def test_batch02_4():
    path = '../resource/预解析优化文件/batch02/IQP202006170000361316_罗燕飞的交易明细20200426174941.pdf'
    return pre_parse(path), ['兴业银⾏', '6229****6211*', '罗燕飞']


@preparse_assert
def test_batch02_5():
    path = '../resource/预解析优化文件/batch02/3.10    4ab75341-c546-4f4d-8eba-1a11e4ea6ec0.pdf'
    return pre_parse(path), ['青岛银行', '6231***********3269', '梅青']


@preparse_assert
def test_batch02_6():
    path = '../resource/预解析优化文件/batch02/3.12   1651235577263_二 雅2022.1-3.pdf'
    return pre_parse(path), ['中国建设银行', '', '武汉安盛旺宏建筑劳务有限公司']


@preparse_assert
def test_batch02_7():
    path = '../resource/预解析优化文件/batch02/3.15   201910中国银行对账单.pdf'
    return pre_parse(path), ['中国银行上海市惠南镇支行', '433860029951', '上海龙奋机械设备有限公司']


@preparse_assert
def test_batch02_8():
    path = '../resource/预解析优化文件/batch02/3.14   招行201902流水.pdf'
    return pre_parse(path), ['', '', '']


@preparse_assert
def test_batch02_9():
    path = '../resource/预解析优化文件/batch02/3.17    宏鹏智能建行公户8月.pdf'
    return pre_parse(path), ['中国建设银行', '', '湖北宏鹏智能科技有限公司']


@preparse_assert
def test_batch02_10():
    path = '../resource/预解析优化文件/batch02/3.18   宁波银行最近6个个月202004BB(1).pdf'
    return pre_parse(path), ['', '', '']


@preparse_assert
def test_batch03_01():
    path = '../resource/预解析优化文件/batch03/3.20   食品科技建行公帐20220901-0930.xls'
    return pre_parse(path), ['', '43050175413600000838', '湖南山羊叔叔食品科技有限公司']


@preparse_assert
def test_batch03_02():
    path = '../resource/预解析优化文件/batch03/3.21    2022年6月刘迎春民生2668银行流水明细.xlsx'
    return pre_parse(path), ['', '6226193100062668', '刘迎春']


@preparse_assert
def test_batch03_03():
    path = '../resource/预解析优化文件/batch03/3.22    22年9月刘迎春邮政5643银行流水明细.xlsx'
    return pre_parse(path), ['', '6217995510024455643', '']


@preparse_assert
def test_batch03_04():
    path = '../resource/预解析优化文件/batch03/3.23    23年4月湘东8010公账银行流水.xlsx'
    return pre_parse(path), ['', '', '']
    # 账户及账号非通用格式，不做处理


@preparse_assert
def test_batch03_05():
    path = '../resource/预解析优化文件/batch03/3.24    建设高新0192.xlsx'
    return pre_parse(path), ['', '1020801021001170192', '安徽皖云建设工程有限公司']


@preparse_assert
def test_batch03_06():
    path = '../resource/预解析优化文件/batch03/3.25     农商行流水.xlsx'
    return pre_parse(path), ['', '32438708080074424', '上海陶胜建筑材料有限公司']


@preparse_assert
def test_batch03_07():
    path = '../resource/预解析优化文件/batch03/3.26    532906374710988-20220324-20230324.pdf'
    return pre_parse(path), ['', '', '青岛绘梦师教育科技有限公司']


@preparse_assert
def test_batch03_08():
    path = '../resource/预解析优化文件/batch03/3.27    20230531163509.pdf'
    return pre_parse(path), ['', '', '']


@preparse_assert
def test_batch03_09():
    path = '../resource/预解析优化文件/batch03/1089950598897500160..pdf'
    return pre_parse(path), ['平安银行', '6230580000181960928', '许建磊']


@preparse_assert
def test_batch03_10():
    path = '../resource/预解析优化文件/batch03/1089950598897500160..pdf'
    return pre_parse(path), ['平安银行', '6230580000181960928', '许建磊']


def test_reg():
    ch = '账号: 烟台535904270 210111人民币山东乐塔生物科技有限公司 账号名: 山东乐塔生物科技有限公司'
    m = regex.search(r'[a-zA-Z0-9]+[a-zA-Z0-9\@\.\-\_\*\s]+', ch)
    print(m)
    print(m.group())
