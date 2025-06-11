# API Control for Excel - LLM Integration

A powerful VBA script that enables seamless integration between Excel and Large Language Models (LLMs) with intelligent API call management and automatic monitoring.

## 🚀 Features

### Core Functionality
- **Excel UDF Integration**: Use `=LLM("your prompt")` directly in Excel cells
- **Automatic API Call Counting**: Real-time monitoring of API usage
- **Smart Caching**: Avoid duplicate API calls with intelligent result caching
- **Configurable Limits**: Set maximum API call limits to control usage
- **Real-time Updates**: 2-second refresh interval for instant feedback

### Advanced Features
- **Status Change Detection**: Automatically resets counter when switching from FALSE to TRUE
- **Continuous Monitoring**: Timer never stops, allowing full control recovery
- **One-time Notifications**: Smart alerting that doesn't spam with repeated messages
- **Multiple LLM Support**: Compatible with LM Studio, OpenAI, OpenRouter, and more
- **Error Handling**: Robust error handling with descriptive error messages

## 📋 Requirements

- **Microsoft Excel** (Windows version with VBA support)
- **Windows 10/11** (tested on Windows 11)
- **LLM API Access**: 
  - Local: LM Studio
  - Cloud: OpenAI, OpenRouter, or compatible APIs
- **Network Connection** (for API calls)

## 🛠️ Quick Setup

### 1. Import the Script
1. Open Excel
2. Press `Alt + F11` to open VBA Editor
3. Right-click on your workbook in Project Explorer
4. Choose `Insert > Module`
5. Copy the entire content of `APIControl.vbs` into the module
6. Save your workbook as `.xlsm` (macro-enabled)

### 2. Configure API Settings
Edit the configuration block in the script:

```vba
' LM Studio (Local)
Public Const API_ENDPOINT = "http://localhost:1234/v1/chat/completions"
Public Const API_KEY = ""  ' Leave blank for LM Studio
Public Const DEFAULT_MODEL = "mistral-small-3.1-24b-instruct-2503"

' OR OpenAI (Cloud)
'Public Const API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
'Public Const API_KEY = "your-openai-api-key"
'Public Const DEFAULT_MODEL = "gpt-4o-mini"
```

### 3. Initialize Control Panel
1. Run the `SetupAPIControl` macro (Alt + F8, select SetupAPIControl, Run)
2. This creates a control panel in row 1 of your active sheet

## 🎮 Usage

### Basic LLM Function
```excel
=LLM("What is the capital of France?")
=LLM("Analyze this data", 0.2)
=LLM("Generate creative content", 0.2, "gpt-4o-mini")
```

### Function Parameters
- **prompt** (required): Your question or instruction
- **temperature** (optional): Creativity level (0.0-1.0, default: 0.1)
- **model** (optional): Specific model to use (default: configured model)

### Control Panel

| Call APIs | TRUE/FALSE | Max Calls | 50 | Current Calls | 0 |
|-----------|------------|-----------|----|--------------|----|

- **Call APIs**: Toggle to enable/disable API calls
- **Max Calls**: Set your usage limit
- **Current Calls**: Real-time counter (updates every 2 seconds)

## ⚙️ Configuration Options

### API Endpoints
The script supports multiple API providers:

```vba
' LM Studio (Local)
Public Const API_ENDPOINT = "http://localhost:1234/v1/chat/completions"

' OpenRouter
Public Const API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
Public Const API_KEY = "sk-or-v1-your-key"

' OpenAI
Public Const API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
Public Const API_KEY = "sk-your-openai-key"
```

### Performance Settings
```vba
Public Const AUTO_UPDATE_INTERVAL_SECONDS = 2  ' Update frequency
Public Const HTTP_TIMEOUTMS = 30000            ' Request timeout
```

## 🔧 Management Functions

### Automatic Functions
- **Continuous Monitoring**: Updates every 2 seconds
- **Smart Reset**: Auto-resets when toggling FALSE→TRUE
- **Limit Protection**: Automatically disables calls when limit reached

### Manual Functions
```vba
ShowMemoryCount()    ' Display unsaved calls in memory
ResetCounter()       ' Reset counter and re-enable calls
StopAutoUpdate()     ' Stop automatic monitoring
StartAutoUpdate()    ' Start automatic monitoring
```

## 🛡️ Smart Features

### Counter Reset Logic
- **Manual Reset**: Use `ResetCounter()` macro
- **Toggle Reset**: Switch from FALSE to TRUE automatically resets
- **Limit Reached**: Only shows notification once, timer continues

### Error Handling
- **No API**: Returns cached results when calls disabled
- **HTTP Errors**: Descriptive error messages
- **Parse Errors**: Clear indication of JSON parsing issues
- **Network Issues**: Timeout handling with graceful degradation

### Caching System
- **Intelligent Caching**: Identical prompts return cached results
- **Memory Efficient**: Uses Windows Dictionary object
- **Cache Key**: Based on prompt + temperature + model

## 📊 Monitoring & Debugging

### Debug Information
- View debug messages in VBA Immediate Window (Ctrl+G)
- Real-time status updates
- API call tracking

### Performance Impact
- **CPU Usage**: Negligible (< 0.1%)
- **Memory Usage**: Minimal (few KB)
- **Excel Impact**: No noticeable performance degradation
- **Network**: Only during actual API calls

## 🔍 Troubleshooting

### Common Issues

**"Control row not found"**
- Run `SetupAPIControl` macro first

**"#NO_API" responses**
- Check if Call APIs is set to TRUE
- Verify you haven't exceeded Max Calls limit

**HTTP errors**
- Verify API endpoint and key
- Check network connectivity
- Confirm API service is running

**Timeouts**
- Increase `HTTP_TIMEOUTMS` value
- Check network stability

### Reset Everything
```vba
Sub FullReset()
    Call StopAutoUpdate
    Call ResetCounter
    ' Delete row 1 and run SetupAPIControl again
End Sub
```

## 📁 File Structure

```
📦 Data_Analyses
├── 📄 APIControl.vbs          # Main VBA script
├── 📄 README.md               # This documentation
└── 📄 LICENSE                 # Apache-2.0 License
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] Support for streaming responses
- [ ] Multiple API endpoint load balancing
- [ ] Usage analytics dashboard
- [ ] Custom function validation
- [ ] Batch processing capabilities

## 💡 Tips & Best Practices

### Optimal Usage
- Use caching effectively by asking similar questions
- Set reasonable temperature values (0.1 for factual, 0.7+ for creative)
- Monitor your API usage regularly
- Use specific models for specialized tasks

### Performance Optimization
- Keep prompts concise but clear
- Use the same prompt phrasing for cache hits
- Set appropriate timeouts for your network
- Regular cleanup of old workbooks

### Security
- Store API keys securely
- Use environment variables for production
- Regularly rotate API keys
- Monitor API usage for unexpected spikes

---

**Created with ❤️ for seamless Excel-LLM integration**

For support, please open an issue on [GitHub](https://github.com/vcentea/Data_Analyses/issues). 