"""
与apriori唯一不同的是:runApriori()函数，新增了提升度的计算
同时生成的表格之中，有每两对内容的：支持度、置信度、提升度
"""

import sys

from itertools import chain, combinations
from collections import defaultdict
from optparse import OptionParser
from tqdm import tqdm
import pandas as pd

class apriori():
    
    def subsets(self,arr):
        """ Returns non empty subsets of arr"""
        return chain(*[combinations(arr, i + 1) for i, a in enumerate(arr)])
    
    
    def returnItemsWithMinSupport(self,itemSet, transactionList, minSupport, freqSet,count = 100000):
        # 最耗时    
        """
        calculates the support for items in the itemSet and returns a subset
           of the itemSet each of whose elements satisfies the minimum support
        """
        _itemSet = set()
        localSet = defaultdict(int)
        
        n = 0
        for item in tqdm(itemSet):
        # time cost
            for transaction in transactionList:
                    if item.issubset(transaction):
                            freqSet[item] += 1
                            localSet[item] += 1
            n += 1
            if n >= count:
                break

        for item, count in list(localSet.items()):
                support = float(count)/len(transactionList)

                if support >= minSupport:
                        _itemSet.add(item)

        return _itemSet
    
    
    def joinSet(self,itemSet, length):
            """Join a set with itself and returns the n-element itemsets"""
            return set([i.union(j) for i in itemSet for j in itemSet if len(i.union(j)) == length])
    
    
    def getItemSetTransactionList(self,data_iterator):
        transactionList = list()
        itemSet = set()
        print('Generate 1-itemSets ... ')
        for record in data_iterator:
            transaction = frozenset(record)
            transactionList.append(transaction)
            for item in transaction:
                itemSet.add(frozenset([item]))              # Generate 1-itemSets
        return itemSet, transactionList
    
    
    def runApriori(self,data_iter, minSupport, minConfidence,minLift = 0,tuples =2,count = 100000):
        """
        run the apriori algorithm. data_iter is a record iterator
        Return both:
         - items (tuple, support)
         - rules (element,remain, posttuple, support,confidence,lift)
         - minSupport - 支持度
         - minConfidence - 置信度
         - minLift - 提升度
         - tuples = 2 支持输出对数,2代表只支持(a,b),(b,c)这样的
         - count = 100000,至多遍历数据量,为了防止数据量过大
         
         其中:
             - element:前置项词
             - remain:(前置项词,后置项词)
             - posttuple:后置项词
             - support:支持度
             - confidence:置信度
             - lift:提升度
        exa:
             (
                 (('皇马',), ('利物浦',)),
                 ('利物浦', '皇马'),
                 0.0012195121951219512,
                 0.25,
                 51.25
             )
        """
        itemSet, transactionList = self.getItemSetTransactionList(data_iter)
        
        freqSet = defaultdict(int)
        largeSet = dict()
        # Global dictionary which stores (key=n-itemSets,value=support)
        # which satisfy minSupport
    
        assocRules = dict()
        # Dictionary which stores Association Rules

        oneCSet = self.returnItemsWithMinSupport(itemSet,
                                            transactionList,
                                            minSupport,
                                            freqSet,
                                            count = count)

        currentLSet = oneCSet
        k = 2
        while(currentLSet != set([])):
            largeSet[k-1] = currentLSet
            currentLSet = self.joinSet(currentLSet, k)
            currentCSet = self.returnItemsWithMinSupport(currentLSet,
                                                    transactionList,
                                                    minSupport,
                                                    freqSet,
                                                    count = count)
            currentLSet = currentCSet
            k = k + 1

        def getSupport(item):
                """local function which Returns the support of an item"""
                return float(freqSet[item])/len(transactionList)
        print('Calculation the tuple words and support ... ')
        toRetItems = []
        for key, value in list(largeSet.items()):
            toRetItems.extend([(tuple(item), getSupport(item))
                               for item in value])
    
        toRetRules = []
        print('Calculation the pretuple words and confidence ... ')
        for key, value in list(largeSet.items())[1:]:
            for item in value:
                if len(item) <= tuples:
                    _subsets = map(frozenset, [x for x in self.subsets(item)])
                    for element in _subsets:
                        remain = item.difference(element)
                        if len(remain) > 0:
                            confidence = getSupport(item)/getSupport(element)
                            #lift = getSupport(item)/( getSupport(element) * getSupport(remain))
                            lift = confidence / getSupport(remain)
                            self_support = getSupport(item)
                            if self_support >= minSupport:
                                if confidence >= minConfidence:
                                    if confidence >= minLift:
                                        toRetRules.append(((tuple(element), tuple(remain)),tuple(item),
                                                           self_support,confidence,lift))
        return toRetItems, toRetRules
    
    
    def printResults(self,items, rules):
        """prints the generated itemsets sorted by support and the confidence rules sorted by confidence"""
        for item, support in sorted(items):
            print ("item: %s , %.3f" % (str(item), support))
        print ("\n------------------------ RULES:")
        for rule,remain,support,confidence,lift in sorted(rules):
            pre, post = rule
            print( "Rule: %s ==> %s , %.3f" % (str(pre), str(post), confidence))

    
    def dataFromFile(self,fname,extra = False):
        """Function which reads from the file and yields a generator"""
        if not extra:
        # 不是本地读入
            file_iter = open(fname, encoding = 'utf-8')
            for line in file_iter:
                line = line.strip().rstrip(',')                         # Remove trailing comma
                record = frozenset(line.split(','))
                yield record
        else:
            for n in range(len(fname)):
                record = frozenset(fname.ix[n,:])
                yield record
    
    def dataFromList(self,data_list):
        for dl in data_list:
            yield frozenset(dl)
    
                
    def transferDataFrame(self,items, rules,removal = True):
        '''把内容转变为dataframe格式'''
        # 无向
        items_data = pd.DataFrame(items)
        items_data.columns = ['word','support']
        items_data['len'] = list(map(len,items_data.word))
        
        # 有向
        rules_data = pd.DataFrame(rules)
        rules_data.columns = ['word','item','support','confidence','lift']
        rules_data['word_x'] = list(map(lambda x : x[0][0] if len(x[0])==1 else x[0], rules_data.word))
        rules_data['word_y'] = list(map(lambda x : x[1][0] if len(x[1])==1 else x[1], rules_data.word))
        rules_data['item_len'] = list(map(len,rules_data['item']))
        
        # 去重
        if removal:
            rules_data['word_xy'] = list(map(lambda x : ''.join(list(set([x[0][0],x[1][0]]))), rules_data.word))
            rules_data = rules_data.drop_duplicates(['word_xy'])   
        
        return items_data,rules_data[['word_x','word_y','item','item_len','support','confidence','lift']]
    

if __name__ == "__main__":
    # 初始化
    apr = apriori()
    
    # ------------ 1 本地直接导入  ------------
    inFile = apr.dataFromFile('INTEGRATED-DATASET.csv',extra = False)
    minSupport = 0.15
    minConfidence = 0.3
    items, rules = apr.runApriori(inFile, minSupport, minConfidence,tuples = 2)
    #     - items (tuple, support)
    #     - rules ((pretuple, posttuple), confidence)
    
    # ------------ 2 先编译再导入  ------------
    data = pd.read_csv('CoOccurrence_data_800.csv',header = None)
    inFile = apr.dataFromFile(data[[1,2]],extra = True)
    #data_iter = apr.dataFromFile(data[[1,2]],extra = True)

    #list(inFile)
    minSupport = 0.0
    minConfidence = 0.0
    minLift = 0.0
    items, rules = apr.runApriori(inFile, minSupport, minConfidence,minLift,tuples = 2,count = 50000)
    print('--------items number is: %s , rules number is : %s--------'%(len(items),len(rules)))
    
    
    # ------------ 3 list导入:不等长 ------------
    data_list = [['迈汽车', '售后服务'],
    ['英菲尼迪', '雷克萨斯'],
    ['张文钊', '球衣','张文钊', '球衣'],
    ['奥林匹克竞赛', '高考加分','奥林匹克竞赛', '高考加分']]

    inFile = apr.dataFromList(data_list)
    items, rules = apr.runApriori(inFile, minSupport, minConfidence,minLift,tuples = 2)
    print('--------items number is: %s , rules number is : %s--------'%(len(items),len(rules)))

    # ------------ print函数 ------------
    apr.printResults(items, rules)
    
    # ------------ dataframe------------ 
    items_data,rules_data = apr.transferDataFrame(items, rules)

    
    
