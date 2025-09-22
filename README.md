# 多智能體投資公司專案

此專案依照規劃書實作出一個可運行的「AI 驅動投資研究部」雛形，透過多個代理人（技術、基本面、情緒與風控）來蒐集資訊、彙整意見，最後由投資組合經理輸出標準化的投資決策 JSON，並對決策進行簡易回測。

## 專案亮點

- **多代理人架構**：每個代理人各司其職，輸出評分與理由，模擬真實投資公司會議流程。
- **資料擷取**：透過 `yfinance` 下載股價、財務資料與新聞資訊，自動轉換成代理人所需的上下文。
- **技術指標計算**：計算移動平均、RSI、MACD、布林通道等指標，用於技術分析決策。
- **風險控管**：風控官根據波動度設定倉位限制，避免過度曝險。
- **回測模組**：根據決策 JSON 快速估算報酬、Sharpe ratio 與最大回撤。

## 安裝與環境

```bash
pip install -r requirements.txt
```

必要套件：

- pandas
- numpy
- yfinance
- python-dotenv（選用，便於載入 `.env`）

### 環境變數設定

專案在根目錄提供了預設的 `.env` 檔案，可作為設定 LLM 供應商、API key 與模型等參數的範本：

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024
```

若需啟用真實的 LLM 代理人，請將 `OPENROUTER_API_KEY` 或 `LLM_API_KEY` 改為有效的金鑰，並依需求調整模型與其他參數。程式會自動讀取 `.env`（若安裝 `python-dotenv`）或直接從系統環境變數載入設定，並會依序偵測 `LLM_API_KEY`、`OPENROUTER_API_KEY` 與 `OPENAI_API_KEY`。

## 使用方式

```bash
python main.py AAPL MSFT --start 2023-01-01 --end 2023-12-31 --output decisions.json
```

上述指令會下載指定標的在時間區間內的資料，召開一次「投資會議」，並將最終的投資決策（含各代理人報告與回測結果）輸出成 JSON。

## 輸出範例

```json
{
  "AAPL": {
    "as_of": "2023-12-29",
    "symbol": "AAPL",
    "composite_score": 0.42,
    "orders": [
      {
        "symbol": "AAPL",
        "action": "buy",
        "weight": 0.08,
        "entry_rule": "SMA20>SMA50 & MACD histogram positive",
        "stop": 0.08,
        "take_profit": 0.2,
        "rationale": "...整合各代理人理由..."
      }
    ],
    "max_gross_exposure": 1.0,
    "notes": "Diversify across sectors; keep tech exposure <50%",
    "agent_reports": [
      {
        "agent": "Technical Analyst",
        "score": 0.35,
        "rationale": "SMA20 above SMA50; MACD histogram positive; ..."
      },
      {
        "agent": "Fundamental Analyst",
        "score": 0.12,
        "rationale": "PE attractive ..."
      }
    ],
    "backtest": {
      "total_return": 0.11,
      "sharpe_ratio": 1.02,
      "max_drawdown": -0.07
    }
  }
}
```

## 架構與流程

1. `InvestmentMeeting` 下載資料並建立 `AnalysisContext`。
2. 依序呼叫各代理人 `analyze` 方法產出報告。
3. 投資組合經理 `PortfolioManager.synthesize` 統整報告，輸出投資決策 JSON。
4. `backtest_portfolio` 根據決策進行簡易回測，產出績效指標。

## 下一步建議

- 整合 OpenRouter / AutoGen 以真實 LLM 對話驅動代理人分析。
- 將回測模組替換為 Backtrader 或 vectorbt 以提升準確度。
- 擴充情緒分析，導入 finBERT 或即時社群資料。
- 增加每日/每週自動產出 PDF 或儀表板報告。

此專案提供完整骨架與可執行的 MVP，方便持續擴充成全自動化的投資研究流程。
