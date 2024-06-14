# import hanlp
# HanLP = hanlp.pipeline() \
#     .append(hanlp.utils.rules.split_sentence, output_key='sentences') \
#     .append(hanlp.load('FINE_ELECTRA_SMALL_ZH'), output_key='tok') \
#     .append(hanlp.load('CTB9_POS_ELECTRA_SMALL'), output_key='pos') \
#     .append(hanlp.load('MSRA_NER_ELECTRA_SMALL_ZH'), output_key='ner', input_key='tok') \
#     .append(hanlp.load('CTB9_DEP_ELECTRA_SMALL', conll=0), output_key='dep', input_key='tok')\
#     .append(hanlp.load('CTB9_CON_ELECTRA_SMALL'), output_key='con', input_key='tok')
# print(HanLP('''据360公司官微消息，6月6日，360AI新品发布会暨开发者沟通会在京举办，会员体系“360AI大会员”正式上线。360AI大会员体系采用会员订阅模式，该会员服务覆盖图片、写作、文档、视频、文档模板等五大场景100多款实用工具，可通过360旗下多款浏览器开通“360AI大会员”，即可解锁全部应用。
# '''))


import pkuseg
seg = pkuseg.pkuseg(user_dict="/Users/bytedance/RiderProjects/k-spider-dotnet/k-spider-dotnet-test/dic",postag=True)  # 开启词性标注功能
text = seg.cut("据360公司官微消息，6月6日，360AI新品发布会暨开发者沟通会在京举办，会员体系“360AI大会员”正式上线。360AI大会员体系采用会员订阅模式，该会员服务覆盖图片、写作、文档、视频、文档模板等五大场景100多款实用工具，可通过360旗下多款浏览器开通“360AI大会员”，即可解锁全部应用。\n")
print(text)