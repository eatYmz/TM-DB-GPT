// import { Informations, InformationsResponse } from '@/types/information';
// import { GET, POST, PUT, DELETE } from '../index';

// export const getInformation = () => {
//   return GET<object, InformationsResponse[]>(`/v1/information/list`,{});
// };


import { GET, POST } from '../index';
import { InformationResponse, InformationRequest } from '@/types/information';

// 搜索资讯
export const searchInformation = (params: InformationRequest) => {
  console.log('Sending search request with params:', params); // 添加请求日志
  return POST<InformationRequest, InformationResponse>('/api/v1/information/search', params)
    .then(response => {
      console.log('Received search response:', response); // 添加响应日志
      return response;
    })
    .catch(error => {
      console.error('Search request failed:', error); // 添加错误日志
      throw error;
    });
};