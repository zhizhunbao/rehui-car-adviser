import React, { ReactNode, useState, useCallback, useEffect, useRef } from 'react';
import { SearchContext } from './SearchContext';
import { 
  SearchResult, 
  SearchContextType, 
  SearchRequest, 
  SearchFilters, 
  SearchSort,
  WebSocketMessage,
  SearchResponse
} from '../../types';
import { apiService } from '../../services/api';
import { WebSocketService } from '../../services/websocket/websocketService';
import { logger } from '../../utils/logger';

interface SearchProviderProps {
  children: ReactNode;
}

export const SearchProvider: React.FC<SearchProviderProps> = ({ children }) => {
  // 状态管理
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [hasMore, setHasMore] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [sort, setSort] = useState<SearchSort>({ field: 'created_at', order: 'desc' });
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  
  // WebSocket 服务引用
  const wsServiceRef = useRef<WebSocketService | null>(null);
  const streamingResultsRef = useRef<SearchResult[]>([]);

  // 初始化 WebSocket 连接
  useEffect(() => {
    const initWebSocket = async () => {
      try {
        const wsService = new WebSocketService({
          url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
          reconnectInterval: 5000,
          maxReconnectAttempts: 5,
          heartbeatInterval: 30000,
        });

        // 订阅搜索结果
        wsService.subscribe('search', (data: any) => {
          handleStreamingSearch(data);
        });

        // 订阅搜索建议
        wsService.subscribe('search_suggestions', (data: any) => {
          if (data.suggestions) {
            setSuggestions(data.suggestions);
          }
        });

        // 订阅错误消息
        wsService.subscribe('error', (data: any) => {
          logger.logResult("WebSocket错误", data.message || "未知错误");
          setError(data.message || "搜索连接出现错误");
          setIsStreaming(false);
        });

        await wsService.connect();
        wsServiceRef.current = wsService;
        
        logger.logResult("WebSocket初始化", "搜索服务连接成功");
      } catch (error) {
        logger.logResult("WebSocket初始化失败", error.toString());
        // WebSocket 连接失败不影响基本功能，继续使用 HTTP API
      }
    };

    initWebSocket();

    // 清理函数
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.destroy();
        wsServiceRef.current = null;
      }
    };
  }, []);

  // 处理流式搜索结果
  const handleStreamingSearch = useCallback((data: any) => {
    if (data.type === 'search_results') {
      streamingResultsRef.current = [...streamingResultsRef.current, ...data.results];
      setResults(streamingResultsRef.current);
      setTotal(data.total || streamingResultsRef.current.length);
      setHasMore(data.hasMore || false);
      
      logger.logResult("流式搜索结果", `收到${data.results.length}条结果`);
    } else if (data.type === 'search_complete') {
      setIsStreaming(false);
      streamingResultsRef.current = [];
      
      logger.logResult("搜索完成", `总共${data.total}条结果`);
    }
  }, []);

  // 执行搜索
  const search = useCallback(async (request: SearchRequest) => {
    logger.logResult("开始搜索", `查询: ${request.query}`);
    
    if (!request.query.trim()) {
      logger.logResult("搜索失败", "查询内容为空");
      setError('请输入搜索内容');
      return;
    }

    setIsLoading(true);
    setError(null);
    setQuery(request.query);
    
    // 重置分页
    if (request.pagination?.page === 1) {
      setResults([]);
      setPage(1);
      streamingResultsRef.current = [];
    }

    try {
      // 优先使用 WebSocket 实时搜索
      if (wsServiceRef.current?.isConnected() && request.query.length > 2) {
        setIsStreaming(true);
        
        // 通过 WebSocket 发送搜索请求
        const wsMessage: WebSocketMessage = {
          id: `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          type: 'search',
          action: 'start',
          data: {
            query: request.query,
            filters: request.filters || filters,
            sort: request.sort || sort,
            pagination: request.pagination || { page, limit }
          },
          timestamp: new Date().toISOString()
        };

        wsServiceRef.current.sendMessage('search', wsMessage);
        logger.logResult("WebSocket搜索", `查询: ${request.query}`);
      } else {
        // 回退到 HTTP API
        logger.logResult("WebSocket未连接", "使用HTTP API搜索");
        
        const response = await apiService.searchCars(request.query);
        
        if (response.results) {
          setResults(response.results);
          setTotal(response.total);
          setPage(response.page);
          setLimit(response.limit);
          setHasMore(response.hasMore);
          
          if (response.suggestions) {
            setSuggestions(response.suggestions);
          }
          
          logger.logResult("HTTP搜索成功", `返回${response.results.length}条结果`);
        } else {
          throw new Error('搜索失败');
        }
      }
      
      // 添加到搜索历史
      addToHistory(request.query);
      
    } catch (err: any) {
      logger.logResult("搜索失败", `错误: ${err.message}`);
      setError(err.message || '搜索过程中发生错误');
    } finally {
      setIsLoading(false);
    }
  }, [filters, sort, page, limit]);

  // 加载更多结果
  const loadMore = useCallback(async () => {
    if (!hasMore || isLoading) return;
    
    const nextPage = page + 1;
    logger.logResult("加载更多", `第${nextPage}页`);
    
    try {
      const response = await apiService.searchCars(query);
      
      if (response.results) {
        setResults(prev => [...prev, ...response.results]);
        setPage(response.page);
        setHasMore(response.hasMore);
        
        logger.logResult("加载更多成功", `新增${response.results.length}条结果`);
      }
    } catch (err: any) {
      logger.logResult("加载更多失败", err.message);
      setError('加载更多结果失败');
    }
  }, [hasMore, isLoading, page, query]);

  // 设置查询
  const handleSetQuery = useCallback((newQuery: string) => {
    setQuery(newQuery);
    
    // 实时搜索建议
    if (newQuery.length > 1 && wsServiceRef.current?.isConnected()) {
      const wsMessage: WebSocketMessage = {
        id: `suggest_${Date.now()}`,
        type: 'search',
        action: 'suggestions',
        data: { query: newQuery },
        timestamp: new Date().toISOString()
      };
      
      wsServiceRef.current.sendMessage('search_suggestions', wsMessage);
    }
  }, []);

  // 设置过滤器
  const handleSetFilters = useCallback((newFilters: SearchFilters) => {
    setFilters(newFilters);
    logger.logResult("设置过滤器", JSON.stringify(newFilters));
  }, []);

  // 设置排序
  const handleSetSort = useCallback((newSort: SearchSort) => {
    setSort(newSort);
    logger.logResult("设置排序", `${newSort.field} ${newSort.order}`);
  }, []);

  // 清除过滤器
  const clearFilters = useCallback(() => {
    setFilters({});
    logger.logResult("清除过滤器", "重置所有过滤器");
  }, []);

  // 清除结果
  const clearResults = useCallback(() => {
    setResults([]);
    setQuery('');
    setTotal(0);
    setPage(1);
    setHasMore(false);
    setError(null);
    logger.logResult("清除结果", "重置搜索结果");
  }, []);

  // 添加到历史记录
  const addToHistory = useCallback((query: string) => {
    setSearchHistory(prev => {
      const newHistory = [query, ...prev.filter(item => item !== query)];
      return newHistory.slice(0, 10); // 最多保存10条历史
    });
  }, []);

  // 清除历史记录
  const clearHistory = useCallback(() => {
    setSearchHistory([]);
    logger.logResult("清除历史", "清空搜索历史");
  }, []);

  const value: SearchContextType = {
    query,
    results,
    isLoading,
    error,
    total,
    page,
    limit,
    hasMore,
    filters,
    sort,
    suggestions,
    searchHistory,
    search,
    loadMore,
    setQuery: handleSetQuery,
    setFilters: handleSetFilters,
    setSort: handleSetSort,
    clearFilters,
    clearResults,
    addToHistory,
    clearHistory,
  };

  return (
    <SearchContext.Provider value={value}>
      {children}
    </SearchContext.Provider>
  );
};
