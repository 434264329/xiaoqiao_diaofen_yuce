class FansChart {
    constructor() {
        this.chart = null;
        this.data = [];
        this.linearModel = null;
        this.exponentialModel = null;
    }

    async init() {
        try {
            console.log('开始初始化图表系统...');
            
            // 加载数据
            this.loadData();
            console.log('数据加载完成');
            
            // 计算模型
            this.calculateLinearRegression();
            console.log('线性回归计算完成');
            
            this.calculateExponentialDecay();
            console.log('指数衰减计算完成');
            
            // 创建图表
            this.createChart();
            console.log('图表创建完成');
            
        } catch (error) {
            console.error('图表初始化失败:', error);
            throw error;
        }
    }

    loadData() {
        try {
            // 直接使用全局变量 FANS_DATA
            if (typeof FANS_DATA === 'undefined') {
                throw new Error('数据文件未加载');
            }

            console.log('原始数据:', FANS_DATA.length, '条');
            console.log('数据示例:', FANS_DATA.slice(0, 3));

            // 数据清洗和验证
            this.data = FANS_DATA
                .filter(item => {
                    // 检查数据完整性
                    if (!item) return false;
                    
                    // 检查必要字段
                    const hasTime = typeof item.time === 'number' && !isNaN(item.time) && item.time > 0;
                    const hasFans = typeof item.fans === 'number' && !isNaN(item.fans) && item.fans > 0;
                    
                    if (!hasTime || !hasFans) {
                        console.log('过滤无效数据:', item);
                        return false;
                    }
                    
                    return true;
                })
                .map(item => ({
                    timestamp: item.time, // 使用 time 字段作为数字时间戳
                    fans: item.fans,
                    timeString: item.timestamp // 保留原始时间字符串
                }))
                .sort((a, b) => a.timestamp - b.timestamp); // 按时间排序

            console.log('有效数据:', this.data.length, '条');
            
            // 详细的数据检查
            if (this.data.length > 0) {
                console.log('处理后数据示例:', this.data.slice(0, 3));
                console.log('时间范围:', {
                    start: new Date(this.data[0].timestamp).toLocaleString('zh-CN'),
                    end: new Date(this.data[this.data.length - 1].timestamp).toLocaleString('zh-CN')
                });
                console.log('粉丝数范围:', {
                    min: Math.min(...this.data.map(d => d.fans)),
                    max: Math.max(...this.data.map(d => d.fans))
                });
            } else {
                console.error('没有有效数据！');
                console.log('原始数据检查:', {
                    hasData: FANS_DATA.length > 0,
                    firstItem: FANS_DATA[0],
                    timeType: typeof FANS_DATA[0]?.time,
                    fansType: typeof FANS_DATA[0]?.fans,
                    timeValue: FANS_DATA[0]?.time,
                    fansValue: FANS_DATA[0]?.fans
                });
                throw new Error('没有有效数据可用于分析');
            }
            
            if (this.data.length < 10) {
                throw new Error(`有效数据点太少（${this.data.length}个），无法进行预测`);
            }
            
        } catch (error) {
            console.error('数据加载失败:', error);
            throw error;
        }
    }

    calculateLinearRegression() {
        if (this.data.length < 2) {
            console.warn('数据点不足，无法计算线性回归');
            return;
        }

        try {
            const n = this.data.length;
            const startTime = this.data[0].timestamp;
            
            // 将时间转换为天数（从第一个数据点开始）
            const points = this.data.map(d => ({
                x: (d.timestamp - startTime) / (1000 * 60 * 60 * 24), // 转换为天数
                y: d.fans
            }));

            console.log('线性回归数据点示例:', points.slice(0, 5));

            // 计算线性回归
            const sumX = points.reduce((sum, p) => sum + p.x, 0);
            const sumY = points.reduce((sum, p) => sum + p.y, 0);
            const sumXY = points.reduce((sum, p) => sum + p.x * p.y, 0);
            const sumXX = points.reduce((sum, p) => sum + p.x * p.x, 0);

            const denominator = (n * sumXX - sumX * sumX);
            if (Math.abs(denominator) < 1e-10) {
                console.warn('线性回归计算失败：分母接近零');
                return;
            }

            const slope = (n * sumXY - sumX * sumY) / denominator;
            const intercept = (sumY - slope * sumX) / n;

            // 验证计算结果
            if (isNaN(slope) || isNaN(intercept)) {
                console.warn('线性回归计算结果无效:', { slope, intercept });
                return;
            }

            // 计算R²
            const yMean = sumY / n;
            const ssTotal = points.reduce((sum, p) => sum + Math.pow(p.y - yMean, 2), 0);
            const ssResidual = points.reduce((sum, p) => {
                const predicted = slope * p.x + intercept;
                return sum + Math.pow(p.y - predicted, 2);
            }, 0);
            
            const r2 = ssTotal > 0 ? 1 - (ssResidual / ssTotal) : 0;

            this.linearModel = {
                slope,
                intercept,
                r2: Math.max(0, r2), // 确保R²不为负
                startTime,
                equation: `y = ${slope.toFixed(6)}x + ${intercept.toFixed(2)}`,
                predict: (timestamp) => {
                    const days = (timestamp - startTime) / (1000 * 60 * 60 * 24);
                    const result = slope * days + intercept;
                    return Math.max(0, result); // 确保预测值不为负
                }
            };

            console.log('线性回归模型:', this.linearModel);
        } catch (error) {
            console.error('线性回归计算失败:', error);
            this.linearModel = null;
        }
    }

    calculateExponentialDecay() {
        if (this.data.length < 3) {
            console.warn('数据点不足，无法计算指数模型');
            return;
        }

        try {
            console.log('=== 开始指数衰减拟合 ===');
            
            // 1. 数据预处理
            const startTime = this.data[0].timestamp;
            let x = this.data.map(d => (d.timestamp - startTime) / (1000 * 60 * 60 * 24)); // 天数
            let y = this.data.map(d => d.fans);

            console.log(`原始数据点: ${x.length} 个`);
            console.log('粉丝数范围:', Math.min(...y).toFixed(1), '-', Math.max(...y).toFixed(1));
            console.log('时间跨度:', Math.max(...x).toFixed(2), '天');

            // 2. 调整异常值检测阈值，减少异常值移除
            const yMean = y.reduce((sum, val) => sum + val, 0) / y.length;
            const yStd = Math.sqrt(y.reduce((sum, val) => sum + Math.pow(val - yMean, 2), 0) / y.length);
            const threshold = 4; // 从3倍标准差提高到4倍，减少异常值移除
            
            const cleanData = [];
            let outlierCount = 0;
            
            for (let i = 0; i < x.length; i++) {
                const zScore = Math.abs((y[i] - yMean) / yStd);
                if (zScore <= threshold) {
                    cleanData.push({ x: x[i], y: y[i] });
                } else {
                    outlierCount++;
                    if (outlierCount <= 5) {
                        console.log(`移除极端异常值: 索引${i}, 值${y[i]}, Z-score=${zScore.toFixed(2)}`);
                    }
                }
            }

            if (cleanData.length < 10) {
                console.warn('清理异常值后数据点不足，使用原始数据');
                x = this.data.map(d => (d.timestamp - startTime) / (1000 * 60 * 60 * 24));
                y = this.data.map(d => d.fans);
                outlierCount = 0;
            } else {
                x = cleanData.map(d => d.x);
                y = cleanData.map(d => d.y);
            }

            console.log(`使用数据点: ${x.length} 个 (移除了 ${outlierCount} 个极端异常值)`);

            // 3. 改进的指数拟合方法
            const result = this.simpleExponentialFit(x, y);
            
            if (!result) {
                // 如果标准拟合失败，尝试简化模型 (无偏移项c)
                console.log('尝试简化的指数模型拟合 (无偏移项)');
                const simpleResult = this.simpleExponentialFitNoOffset(x, y);
                if (simpleResult) {
                    const { a, lam, r2 } = simpleResult;
                    // 计算模型特征
                    const halfLife = Math.log(2) / lam;
                    const currentTime = x[x.length - 1];
                    const currentDecayRate = -a * lam * Math.exp(-lam * currentTime);

                    this.exponentialModel = {
                        a: a,
                        lam: lam,
                        c: 0, // 无偏移项
                        r2: r2,
                        halfLife: halfLife,
                        currentDecayRate: currentDecayRate,
                        startTime: startTime,
                        dataPoints: x.length,
                        outlierCount: outlierCount,
                        equation: `y = ${a.toFixed(3)} * e^(-${lam.toFixed(6)} * t)`,
                        predict: (timestamp) => {
                            const days = (timestamp - startTime) / (1000 * 60 * 60 * 24);
                            const result = a * Math.exp(-lam * days);
                            return Math.max(0, result);
                        }
                    };
                    console.log('简化指数模型拟合成功:', this.exponentialModel);
                } else {
                    console.warn('指数拟合失败，数据可能不适合指数模型');
                    return;
                }
            } else {
                const { a, lam, c, r2 } = result;

                // 4. 计算模型特征
                const halfLife = Math.log(2) / lam;
                const currentTime = x[x.length - 1];
                const currentDecayRate = -a * lam * Math.exp(-lam * currentTime);

                // 5. 构建模型对象
                this.exponentialModel = {
                    a: a,
                    lam: lam,
                    c: c,
                    r2: r2,
                    halfLife: halfLife,
                    currentDecayRate: currentDecayRate,
                    startTime: startTime,
                    dataPoints: x.length,
                    outlierCount: outlierCount,
                    equation: `y = ${a.toFixed(3)} * e^(-${lam.toFixed(6)} * t) + ${c.toFixed(3)}`,
                    predict: (timestamp) => {
                        const days = (timestamp - startTime) / (1000 * 60 * 60 * 24);
                        const result = a * Math.exp(-lam * days) + c;
                        return Math.max(0, result);
                    }
                };
                console.log('指数模型拟合成功:', this.exponentialModel);
            }

        } catch (error) {
            console.error('指数衰减计算失败:', error);
            this.exponentialModel = null;
        }
    }

    // 完整指数模型拟合 (y = a*e^(-λt) + c)
    simpleExponentialFit(x, y) {
        try {
            // 估计偏移项c (使用最小值作为初始估计)
            const c = Math.min(...y) * 0.9;
            const yAdjusted = y.map(yi => yi - c);
            
            // 确保所有调整后的值为正
            if (yAdjusted.some(v => v <= 0)) {
                console.warn('调整后的数据包含非正值，无法进行对数转换');
                return null;
            }

            // 转换为线性模型: ln(y - c) = ln(a) - λt
            const lnY = yAdjusted.map(v => Math.log(v));
            
            // 线性回归计算
            const n = x.length;
            const sumX = x.reduce((a, b) => a + b, 0);
            const sumLnY = lnY.reduce((a, b) => a + b, 0);
            const sumXLnY = x.reduce((sum, xi, i) => sum + xi * lnY[i], 0);
            const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);

            const denominator = n * sumXX - sumX * sumX;
            if (Math.abs(denominator) < 1e-10) {
                console.warn('指数拟合分母接近零');
                return null;
            }

            // 计算线性系数 (ln(a) 和 -λ)
            const slope = (n * sumXLnY - sumX * sumLnY) / denominator;
            const intercept = (sumLnY - slope * sumX) / n;

            // 转换回指数模型参数
            const a = Math.exp(intercept);
            const lam = -slope;

            // 计算R²值
            const yPred = x.map(xi => a * Math.exp(-lam * xi) + c);
            const yMean = y.reduce((a, b) => a + b, 0) / n;
            const ssTotal = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
            const ssResidual = y.reduce((sum, yi, i) => sum + Math.pow(yi - yPred[i], 2), 0);
            const r2 = ssTotal > 0 ? 1 - (ssResidual / ssTotal) : 0;

            // 验证参数有效性
            if (isNaN(a) || isNaN(lam) || lam <= 0 || a <= 0 || r2 < 0.1) {
                console.warn('指数拟合参数无效:', { a, lam, r2 });
                return null;
            }

            return { a, lam, c, r2 };
        } catch (error) {
            console.error('指数拟合失败:', error);
            return null;
        }
    }

    // 简化的指数模型拟合 (无偏移项 y = a*e^(-λt))
    simpleExponentialFitNoOffset(x, y) {
        try {
            // 确保所有值为正
            if (y.some(v => v <= 0)) {
                return null;
            }

            // 转换为线性模型: ln(y) = ln(a) - λt
            const lnY = y.map(v => Math.log(v));
            
            // 线性回归计算
            const n = x.length;
            const sumX = x.reduce((a, b) => a + b, 0);
            const sumLnY = lnY.reduce((a, b) => a + b, 0);
            const sumXLnY = x.reduce((sum, xi, i) => sum + xi * lnY[i], 0);
            const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);

            const denominator = n * sumXX - sumX * sumX;
            if (Math.abs(denominator) < 1e-10) {
                return null;
            }

            // 计算线性系数
            const slope = (n * sumXLnY - sumX * sumLnY) / denominator;
            const intercept = (sumLnY - slope * sumX) / n;

            // 转换回指数模型参数
            const a = Math.exp(intercept);
            const lam = -slope;

            // 计算R²值
            const yPred = x.map(xi => a * Math.exp(-lam * xi));
            const yMean = y.reduce((a, b) => a + b, 0) / n;
            const ssTotal = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
            const ssResidual = y.reduce((sum, yi, i) => sum + Math.pow(yi - yPred[i], 2), 0);
            const r2 = ssTotal > 0 ? 1 - (ssResidual / ssTotal) : 0;

            if (isNaN(a) || isNaN(lam) || lam <= 0 || a <= 0 || r2 < 0.1) {
                return null;
            }

            return { a, lam, r2 };
        } catch (error) {
            console.error('简化指数拟合失败:', error);
            return null;
        }
    }

    // 添加获取统计数据的方法
    getStats() {
        if (this.data.length === 0) return null;
        
        const start = new Date(this.data[0].timestamp);
        const end = new Date(this.data[this.data.length - 1].timestamp);
        const timeSpan = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + ' 天';
        const fansValues = this.data.map(d => d.fans);
        const maxFans = Math.max(...fansValues).toFixed(1) + ' 万';
        const minFans = Math.min(...fansValues).toFixed(1) + ' 万';
        
        return {
            dataCount: this.data.length,
            timeSpan,
            maxFans,
            minFans
        };
    }

    createChart() {
        // 图表创建逻辑保持不变，确保使用正确的数据
        const ctx = document.getElementById('fansChart').getContext('2d');
        
        // 准备图表数据
        const labels = this.data.map(d => new Date(d.timestamp));
        const fansData = this.data.map(d => d.fans);
        
        // 销毁现有图表
        if (this.chart) {
            this.chart.destroy();
        }
        
        // 创建新图表
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '实际粉丝数',
                    data: fansData,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'yyyy-MM-dd'
                            }
                        },
                        title: {
                            display: true,
                            text: '日期'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '粉丝数 (万)'
                        }
                    }
                }
            }
        });
    }
}