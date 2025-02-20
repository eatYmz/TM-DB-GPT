import { searchInformation } from '@/client/api/information';
// import { useState } from 'react';
import { useRequest } from 'ahooks';
import { Button, Card, Input, List, Select, Spin, message } from 'antd';
import React, { useState } from 'react';
// 导入公众号配置
import SOURCE_OPTIONS from '@/public/config/sourceOptions.json';

// 创建一个源ID到名称的映射
const SOURCE_MAP = Object.fromEntries(SOURCE_OPTIONS.map(option => [option.value, option.label]));

const MODEL_OPTIONS = [
  { label: 'GPT-3.5', value: 'gpt-3.5-turbo' },
  { label: 'GPT-4', value: 'gpt-4' },
  { label: 'Claude', value: 'claude' },
  { label: 'Gemini', value: 'gemini' },
];

const InformationPage: React.FC = () => {
  const [source, setSource] = useState<string>('');
  const [keyword, setKeyword] = useState<string>('');
  const [model, setModel] = useState<string>('gpt-3.5-turbo'); // 默认选择GPT-3.5s

  // 使用useRequest处理API请求
  const {
    data: responseData,
    loading,
    run,
  } = useRequest(searchInformation, {
    manual: true,
    onSuccess: response => {
      console.log('Raw API Response:', response);
      if (!response?.data?.success) {
        message.error('获取数据失败');
      }
    },
    onError: error => {
      console.error('API Error:', error);
      message.error('获取资讯失败：' + error.message);
    },
  });

  // 处理搜索
  const handleSearch = () => {
    if (!source) {
      message.warning('请选择公众号');
      return;
    }
    console.log('Searching with params:', { source, keyword });
    run({
      source,
      keyword,
      // model, // 添加模型参数
      page: 1,
      page_size: 20,
    });
  };

  // 修改数据获取路径以匹配实际响应结构
  const informationList = responseData?.data?.data?.data || [];
  // const total = responseData?.data?.data?.total || 0;

  console.log('Response data:', responseData?.data);
  console.log('Information list:', informationList);

  // 格式化日期
  // const formatDate = (dateString: string) => {
  //   if (!dateString) return '';
  //   try {
  //     const date = new Date(dateString);
  //     return date.toLocaleDateString('zh-CN', {
  //       year: 'numeric',
  //       month: 'long',
  //       day: 'numeric',
  //     });
  //   } catch {
  //     return '发布时间未知';
  //   }
  // };

  // 获取来源的显示名称
  const getSourceLabel = (sourceId: string) => {
    return SOURCE_MAP[sourceId] || sourceId;
  };

  const isProduction = process.env.NODE_ENV === 'production';

  if (!isProduction) {
    console.log(
      'Debug info:',
      JSON.stringify(
        {
          hasResponse: !!responseData,
          hasData: !!responseData?.data?.data?.data,
          listLength: informationList?.length,
        },
        null,
        2,
      ),
    );
  }

  return (
    <div className='p-6' style={{ height: '80vh', overflowY: 'auto' }}>
      <div className='mb-6 flex gap-4'>
        {/* 公众号选择 */}
        <Select
          className='w-48'
          placeholder='选择公众号'
          options={SOURCE_OPTIONS}
          value={source}
          onChange={setSource}
        />

        {/* 模型选择 */}
        <Select className='w-48' placeholder='选择模型' options={MODEL_OPTIONS} value={model} onChange={setModel} />

        {/* 关键词搜索 */}
        <Input
          className='w-64'
          placeholder='输入关键词'
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          onPressEnter={handleSearch}
        />

        {/* 搜索按钮 */}
        <Button type='primary' onClick={handleSearch} loading={loading}>
          搜索
        </Button>
      </div>
      {/* 结果统计
      {informationList.length > 0 && (
        <div className='mb-4 text-gray-600'>共找到 {total} 条相关资讯</div>
      )} */}

      {/* 资讯列表 */}
      <Spin spinning={loading}>
        {Array.isArray(informationList) && informationList.length > 0 ? (
          <List
            dataSource={informationList}
            renderItem={(item: any) => (
              <List.Item>
                <Card className='w-full hover:shadow-lg transition-shadow'>
                  <div className='flex flex-col gap-2'>
                    {/* 标题 */}
                    <h3 className='text-lg font-bold'>
                      <a href={item.url} target='_blank' rel='noopener noreferrer'>
                        {item.title}
                      </a>
                    </h3>

                    {/* 摘要 */}
                    <p className='text-gray-600 line-clamp-3'>{item.summary}</p>

                    {/* 日期 */}
                    <div className='flex justify-between items-center text-sm text-gray-400'>
                      {/* <span>{formatDate(item.publish_date)}</span> */}
                      <span>来源: {getSourceLabel(item.source)}</span>
                    </div>
                  </div>
                </Card>
              </List.Item>
            )}
          />
        ) : (
          !loading && <div className='text-center text-gray-500 mt-8'>暂无数据</div>
        )}
      </Spin>
    </div>
  );
};

export default InformationPage;
