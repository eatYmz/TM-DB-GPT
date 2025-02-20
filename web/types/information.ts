export interface InformationRequest {
  source: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface InformationItem {
  title: string;
  url: string;
  source: string;
  publish_date: string;
  summary: string;
}

export interface InformationResponse {
  code: string;
  data: {
    data: InformationItem[];
    total: number;
  };
  msg?: string;
}