/**
 * API测试报告生成器 - 生成详细的API测试报告
 */
import type { ApiStats } from './performance'

interface TestCase {
  id: string
  name: string
  description: string
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped'
  duration: number
  error?: string
  details?: any
}

interface TestSuite {
  id: string
  name: string
  description: string
  testCases: TestCase[]
  startTime: number
  endTime?: number
  totalDuration: number
}

interface TestReport {
  id: string
  title: string
  timestamp: number
  environment: string
  testSuites: TestSuite[]
  summary: {
    totalTests: number
    passedTests: number
    failedTests: number
    skippedTests: number
    totalDuration: number
    successRate: number
  }
  performance: ApiStats
  recommendations: string[]
}

class ApiTestReportGenerator {
  private testSuites: TestSuite[] = []
  private currentSuite: TestSuite | null = null

  /**
   * 开始新的测试套件
   */
  startTestSuite(id: string, name: string, description: string): TestSuite {
    this.currentSuite = {
      id,
      name,
      description,
      testCases: [],
      startTime: Date.now(),
      totalDuration: 0
    }
    
    this.testSuites.push(this.currentSuite)
    return this.currentSuite
  }

  /**
   * 结束当前测试套件
   */
  endTestSuite(): void {
    if (this.currentSuite) {
      this.currentSuite.endTime = Date.now()
      this.currentSuite.totalDuration = this.currentSuite.endTime - this.currentSuite.startTime
      this.currentSuite = null
    }
  }

  /**
   * 添加测试用例
   */
  addTestCase(testCase: Omit<TestCase, 'id'>): TestCase {
    if (!this.currentSuite) {
      throw new Error('No active test suite. Call startTestSuite() first.')
    }

    const fullTestCase: TestCase = {
      id: `${this.currentSuite.id}_${this.currentSuite.testCases.length + 1}`,
      ...testCase
    }

    this.currentSuite.testCases.push(fullTestCase)
    return fullTestCase
  }

  /**
   * 更新测试用例状态
   */
  updateTestCase(id: string, updates: Partial<TestCase>): void {
    for (const suite of this.testSuites) {
      const testCase = suite.testCases.find(tc => tc.id === id)
      if (testCase) {
        Object.assign(testCase, updates)
        return
      }
    }
  }

  /**
   * 生成测试报告
   */
  generateReport(
    title: string,
    environment: string,
    performance: ApiStats
  ): TestReport {
    const totalTests = this.testSuites.reduce((sum, suite) => sum + suite.testCases.length, 0)
    const passedTests = this.testSuites.reduce(
      (sum, suite) => sum + suite.testCases.filter(tc => tc.status === 'passed').length,
      0
    )
    const failedTests = this.testSuites.reduce(
      (sum, suite) => sum + suite.testCases.filter(tc => tc.status === 'failed').length,
      0
    )
    const skippedTests = this.testSuites.reduce(
      (sum, suite) => sum + suite.testCases.filter(tc => tc.status === 'skipped').length,
      0
    )
    const totalDuration = this.testSuites.reduce((sum, suite) => sum + suite.totalDuration, 0)

    const report: TestReport = {
      id: `report_${Date.now()}`,
      title,
      timestamp: Date.now(),
      environment,
      testSuites: [...this.testSuites],
      summary: {
        totalTests,
        passedTests,
        failedTests,
        skippedTests,
        totalDuration,
        successRate: totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
      },
      performance,
      recommendations: this.generateRecommendations(performance, failedTests, totalTests)
    }

    return report
  }

  /**
   * 生成优化建议
   */
  private generateRecommendations(
    performance: ApiStats,
    failedTests: number,
    totalTests: number
  ): string[] {
    const recommendations: string[] = []

    // 性能建议
    if (performance.avgResponseTime > 2000) {
      recommendations.push('API平均响应时间较长，建议优化后端性能或考虑增加缓存')
    }

    if (performance.maxResponseTime > 5000) {
      recommendations.push('检测到超时响应，建议检查网络连接或增加超时时间')
    }

    if (performance.totalRetries > performance.totalRequests * 0.1) {
      recommendations.push('重试次数较多，建议检查网络稳定性或API服务状态')
    }

    // 成功率建议
    const successRate = performance.successRequests / performance.totalRequests * 100
    if (successRate < 95) {
      recommendations.push('API成功率较低，建议检查API服务稳定性和错误处理机制')
    }

    // 测试建议
    if (failedTests > 0) {
      recommendations.push(`${failedTests}个测试失败，建议检查相关API端点和业务逻辑`)
    }

    if (totalTests < 10) {
      recommendations.push('测试覆盖率较低，建议增加更多测试用例')
    }

    // 默认建议
    if (recommendations.length === 0) {
      recommendations.push('所有测试通过，API服务运行良好')
    }

    return recommendations
  }

  /**
   * 导出HTML报告
   */
  exportHtmlReport(report: TestReport): string {
    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${report.title} - API测试报告</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        .header p {
            margin: 0;
            opacity: 0.9;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .summary-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        .summary-card.success .value { color: #27ae60; }
        .summary-card.error .value { color: #e74c3c; }
        .summary-card.warning .value { color: #f39c12; }
        .section {
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section h2 {
            margin: 0 0 20px 0;
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .test-suite {
            margin-bottom: 30px;
            border: 1px solid #eee;
            border-radius: 8px;
            overflow: hidden;
        }
        .test-suite-header {
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        .test-suite-title {
            margin: 0;
            font-size: 18px;
            color: #333;
        }
        .test-suite-desc {
            margin: 5px 0 0 0;
            color: #666;
            font-size: 14px;
        }
        .test-case {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .test-case:last-child {
            border-bottom: none;
        }
        .test-case-name {
            font-weight: 500;
        }
        .test-case-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-passed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-skipped { background: #fff3cd; color: #856404; }
        .status-pending { background: #e2e3e5; color: #6c757d; }
        .recommendations {
            background: #fff3cd;
            border: 1px solid #ffeeba;
            border-radius: 8px;
            padding: 20px;
        }
        .recommendations h3 {
            margin: 0 0 15px 0;
            color: #856404;
        }
        .recommendations ul {
            margin: 0;
            padding-left: 20px;
        }
        .recommendations li {
            margin-bottom: 8px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>${report.title}</h1>
        <p>生成时间: ${new Date(report.timestamp).toLocaleString()}</p>
        <p>测试环境: ${report.environment}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3>总测试数</h3>
            <div class="value">${report.summary.totalTests}</div>
        </div>
        <div class="summary-card success">
            <h3>通过</h3>
            <div class="value">${report.summary.passedTests}</div>
        </div>
        <div class="summary-card error">
            <h3>失败</h3>
            <div class="value">${report.summary.failedTests}</div>
        </div>
        <div class="summary-card warning">
            <h3>跳过</h3>
            <div class="value">${report.summary.skippedTests}</div>
        </div>
        <div class="summary-card">
            <h3>成功率</h3>
            <div class="value">${report.summary.successRate}%</div>
        </div>
        <div class="summary-card">
            <h3>总耗时</h3>
            <div class="value">${Math.round(report.summary.totalDuration / 1000)}s</div>
        </div>
    </div>

    <div class="section">
        <h2>性能指标</h2>
        <div class="summary">
            <div class="summary-card">
                <h3>平均响应时间</h3>
                <div class="value">${report.performance.avgResponseTime}ms</div>
            </div>
            <div class="summary-card">
                <h3>最快响应</h3>
                <div class="value">${report.performance.minResponseTime}ms</div>
            </div>
            <div class="summary-card">
                <h3>最慢响应</h3>
                <div class="value">${report.performance.maxResponseTime}ms</div>
            </div>
            <div class="summary-card">
                <h3>总重试次数</h3>
                <div class="value">${report.performance.totalRetries}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>测试详情</h2>
        ${report.testSuites.map(suite => `
            <div class="test-suite">
                <div class="test-suite-header">
                    <h3 class="test-suite-title">${suite.name}</h3>
                    <p class="test-suite-desc">${suite.description}</p>
                </div>
                ${suite.testCases.map(testCase => `
                    <div class="test-case">
                        <div>
                            <div class="test-case-name">${testCase.name}</div>
                            <div style="font-size: 12px; color: #666;">${testCase.description}</div>
                            ${testCase.error ? `<div style="font-size: 12px; color: #e74c3c; margin-top: 4px;">错误: ${testCase.error}</div>` : ''}
                        </div>
                        <div>
                            <span class="test-case-status status-${testCase.status}">${testCase.status}</span>
                            ${testCase.duration > 0 ? `<div style="font-size: 12px; color: #666; margin-top: 4px;">${testCase.duration}ms</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `).join('')}
    </div>

    <div class="recommendations">
        <h3>🔍 优化建议</h3>
        <ul>
            ${report.recommendations.map(rec => `<li>${rec}</li>`).join('')}
        </ul>
    </div>
</body>
</html>`
  }

  /**
   * 导出JSON报告
   */
  exportJsonReport(report: TestReport): string {
    return JSON.stringify(report, null, 2)
  }

  /**
   * 清空所有测试数据
   */
  clear(): void {
    this.testSuites = []
    this.currentSuite = null
  }
}

// 创建全局测试报告生成器实例
export const apiTestReportGenerator = new ApiTestReportGenerator()

export type { TestCase, TestSuite, TestReport }
