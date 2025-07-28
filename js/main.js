class FansPredictionSystem {
    constructor() {
        this.chart = new FansChart();
        this.currentMethod = 'exponential'; // 默认使用指数衰减模型
        this.initEventListeners();
        this.initSystem();
    }

    async initSystem() {
        try {
            console.log('开始初始化系统...');
            await this.chart.init();
            console.log('图表初始化完成');
            
            // 更新模型显示
            this.updateModelDisplay();
            console.log('模型显示更新完成');
            
            // 更新统计数据显示
            this.updateStatsDisplay();
            console.log('统计数据更新完成');
            
            console.log('系统初始化成功！');
        } catch (error) {
            console.error('系统初始化失败:', error);
        }
    }

    initEventListeners() {
        // 预测方法选择事件
        document.getElementById('predictionMethod').addEventListener('change', (e) => {
            this.currentMethod = e.target.value;
            this.updateModelDisplay();
        });

        // 预测按钮事件
        document.getElementById('predictBtn').addEventListener('click', () => {
            this.predictByDateTime();
        });

        // 反向预测按钮事件
        document.getElementById('reversePredictBtn').addEventListener('click', () => {
            this.predictByFans();
        });

        // 设置默认日期时间
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        document.getElementById('dateInput').value = tomorrow.toISOString().split('T')[0];
        
        // 设置默认时间为当前时间
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0]; // HH:MM:SS格式
        document.getElementById('timeInput').value = timeString;
    }

    // 添加统计数据更新方法
    updateStatsDisplay() {
        const stats = this.chart.getStats();
        if (!stats) return;
        
        document.getElementById('dataCount').textContent = stats.dataCount;
        document.getElementById('timeSpan').textContent = stats.timeSpan;
        document.getElementById('maxFans').textContent = stats.maxFans;
        document.getElementById('minFans').textContent = stats.minFans;
    }

    updateModelDisplay() {
        const titleElement = document.getElementById('currentModelTitle');
        const equationElement = document.getElementById('currentModelEquation');
        const paramsElement = document.getElementById('currentModelParams');

        if (this.currentMethod === 'exponential') {
            titleElement.textContent = '📉 指数衰减模型';
            
            if (this.chart.exponentialModel) {
                const { a, lam, c, r2, equation, halfLife } = this.chart.exponentialModel;
                equationElement.textContent = equation;
                paramsElement.innerHTML = `
                    a = ${a.toFixed(2)} 万<br>
                    λ = ${lam.toFixed(6)} /天<br>
                    c = ${c.toFixed(2)} 万<br>
                    R² = ${r2.toFixed(4)}<br>
                    <small>半衰期: ${halfLife < 1000 ? halfLife.toFixed(1) + ' 天' : '很长'}</small>
                `;
            } else {
                equationElement.textContent = 'y = a × e^(-λt) + c';
                paramsElement.innerHTML = '<span style="color: #ff6b6b;">模型计算失败或不可用</span>';
            }
        } else {
            titleElement.textContent = '📊 线性回归模型';
            
            if (this.chart.linearModel) {
                const { slope, intercept, r2, equation } = this.chart.linearModel;
                equationElement.textContent = equation;
                paramsElement.innerHTML = `
                    斜率 = ${slope.toFixed(6)}<br>
                    截距 = ${intercept.toFixed(2)}<br>
                    R² = ${r2.toFixed(4)}<br>
                    <small>日变化: ${slope > 0 ? '+' : ''}${slope.toFixed(2)} 万/天</small>
                `;
            } else {
                equationElement.textContent = 'y = ax + b';
                paramsElement.innerHTML = '<span style="color: #ff6b6b;">模型计算失败或不可用</span>';
            }
        }
    }

    predictByDateTime() {
        const dateInput = document.getElementById('dateInput').value;
        const timeInput = document.getElementById('timeInput').value;
        const resultElement = document.getElementById('predictionResult');
        
        if (!dateInput || !timeInput) {
            resultElement.innerHTML = '<span style="color: #ff6b6b;">请选择完整的日期和时间</span>';
            return;
        }

        // 组合日期和时间
        const dateTimeString = `${dateInput}T${timeInput}`;
        const targetDate = new Date(dateTimeString);
        const now = new Date();
        
        if (isNaN(targetDate.getTime())) {
            resultElement.innerHTML = '<span style="color: #ff6b6b;">日期时间格式无效</span>';
            return;
        }
        
        if (targetDate <= now) {
            resultElement.innerHTML = '<span style="color: #ff6b6b;">请选择未来的日期时间</span>';
            return;
        }

        // 显示加载状态
        resultElement.innerHTML = '<div class="loading"></div> 计算中...';

        setTimeout(() => {
            let prediction = null;
            let modelUsed = '';
            let modelAvailable = false;

            // 根据用户选择的方法进行预测
            if (this.currentMethod === 'exponential' && this.chart.exponentialModel) {
                prediction = this.chart.exponentialModel.predict(targetDate.getTime());
                modelUsed = '指数衰减模型';
                modelAvailable = true;
            } else if (this.currentMethod === 'linear' && this.chart.linearModel) {
                prediction = this.chart.linearModel.predict(targetDate.getTime());
                modelUsed = '线性回归模型';
                modelAvailable = true;
            } else {
                // 如果选择的模型不可用，尝试使用另一个模型
                if (this.chart.exponentialModel) {
                    prediction = this.chart.exponentialModel.predict(targetDate.getTime());
                    modelUsed = '指数衰减模型（备用）';
                    modelAvailable = true;
                } else if (this.chart.linearModel) {
                    prediction = this.chart.linearModel.predict(targetDate.getTime());
                    modelUsed = '线性回归模型（备用）';
                    modelAvailable = true;
                }
            }

            console.log('预测结果:', { prediction, modelUsed, modelAvailable, targetDate: targetDate.getTime() });

            if (modelAvailable && prediction !== null && !isNaN(prediction) && isFinite(prediction) && prediction >= 0) {
                const confidence = this.calculateConfidence(targetDate);
                const timeFromNow = this.formatTimeFromNow(targetDate);
                
                resultElement.innerHTML = `
                    <div style="font-size: 1.6em; font-weight: bold; margin-bottom: 10px;">
                        ${prediction.toFixed(1)} 万
                    </div>
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">
                        ${targetDate.toLocaleString('zh-CN')}
                    </div>
                    <div style="font-size: 0.85em; opacity: 0.8;">
                        ${timeFromNow}<br>
                        ${modelUsed} | 可信度: ${confidence}%
                    </div>
                `;
            } else {
                let errorMsg = '预测失败';
                if (!modelAvailable) {
                    errorMsg = '所选模型不可用，请检查数据质量';
                } else if (prediction === null || isNaN(prediction)) {
                    errorMsg = '计算结果无效，可能超出模型适用范围';
                } else if (prediction < 0) {
                    errorMsg = '预测值为负数，模型可能不适用于此时间范围';
                }
                
                resultElement.innerHTML = `<span style="color: #ff6b6b;">${errorMsg}</span>`;
            }
        }, 600);
    }

    predictByFans() {
        const fansInput = document.getElementById('fansInput').value;
        const resultElement = document.getElementById('reversePredictionResult');
        
        if (!fansInput || fansInput <= 0) {
            resultElement.innerHTML = '<span style="color: #ff6b6b;">请输入有效的粉丝数</span>';
            return;
        }

        const targetFans = parseFloat(fansInput);
        
        if (isNaN(targetFans)) {
            resultElement.innerHTML = '<span style="color: #ff6b6b;">粉丝数格式无效</span>';
            return;
        }
        
        // 显示加载状态
        resultElement.innerHTML = '<div class="loading"></div> 计算中...';

        setTimeout(() => {
            let predictedDate = null;
            let modelUsed = '';
            let modelAvailable = false;

            // 根据用户选择的方法进行反向预测
            if (this.currentMethod === 'exponential' && this.chart.exponentialModel) {
                predictedDate = this.reversePredictExponential(targetFans);
                modelUsed = '指数衰减模型';
                modelAvailable = true;
            } else if (this.currentMethod === 'linear' && this.chart.linearModel) {
                predictedDate = this.reversePredictLinear(targetFans);
                modelUsed = '线性回归模型';
                modelAvailable = true;
            } else {
                // 如果选择的模型不可用，尝试使用另一个模型
                if (this.chart.exponentialModel) {
                    predictedDate = this.reversePredictExponential(targetFans);
                    modelUsed = '指数衰减模型（备用）';
                    modelAvailable = true;
                } else if (this.chart.linearModel) {
                    predictedDate = this.reversePredictLinear(targetFans);
                    modelUsed = '线性回归模型（备用）';
                    modelAvailable = true;
                }
            }

            console.log('反向预测结果:', { predictedDate, modelUsed, modelAvailable, targetFans });

            if (modelAvailable && predictedDate && !isNaN(predictedDate.getTime()) && predictedDate > new Date()) {
                const timeFromNow = this.formatTimeFromNow(predictedDate);

                resultElement.innerHTML = `
                    <div style="font-size: 1.4em; font-weight: bold; margin-bottom: 10px;">
                        ${predictedDate.toLocaleDateString('zh-CN')}
                    </div>
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">
                        ${predictedDate.toLocaleString('zh-CN')}
                    </div>
                    <div style="font-size: 0.85em; opacity: 0.8;">
                        ${timeFromNow}<br>
                        ${modelUsed}预测达到${targetFans}万粉丝
                    </div>
                `;
            } else {
                let errorMsg = '反向预测失败';
                if (!modelAvailable) {
                    errorMsg = '所选模型不可用，请检查数据质量';
                } else if (!predictedDate || isNaN(predictedDate.getTime())) {
                    errorMsg = '计算结果无效，可能超出模型适用范围';
                } else if (predictedDate <= new Date()) {
                    errorMsg = '预测日期已过，可能已达到该粉丝数';
                }
                
                resultElement.innerHTML = `<span style="color: #ff6b6b;">${errorMsg}</span>`;
            }
        }, 600);
    }

    reversePredictLinear(targetFans) {
        if (!this.chart.linearModel) return null;
        
        const { slope, intercept, startTime } = this.chart.linearModel;
        if (slope === 0) return null;
        
        // 解方程式: targetFans = slope * days + intercept
        const days = (targetFans - intercept) / slope;
        const timestamp = startTime + days * 24 * 60 * 60 * 1000;
        
        return new Date(timestamp);
    }

    reversePredictExponential(targetFans) {
        if (!this.chart.exponentialModel) return null;
        
        const { a, lam, c, startTime } = this.chart.exponentialModel;
        if (lam <= 0) return null;
        
        // 解方程式: targetFans = a*e^(-λt) + c
        const value = targetFans - c;
        if (value <= 0 || value > a * 2) return null; // 超出合理范围
        
        const days = -Math.log(value / a) / lam;
        const timestamp = startTime + days * 24 * 60 * 60 * 1000;
        
        return new Date(timestamp);
    }

    calculateConfidence(targetDate) {
        // 简单的可信度计算，基于预测时间与数据结束时间的距离
        const lastDataDate = new Date(this.chart.data[this.chart.data.length - 1].timestamp);
        const dataRange = lastDataDate - new Date(this.chart.data[0].timestamp);
        const predictionRange = targetDate - lastDataDate;
        
        // 预测时间越远，可信度越低
        let confidence = 100 - (predictionRange / dataRange) * 50;
        return Math.max(30, Math.min(95, Math.round(confidence)));
    }

    formatTimeFromNow(targetDate) {
        const now = new Date();
        const diffMs = targetDate - now;
        
        const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        
        if (days > 0) {
            return `距离现在还有 ${days} 天 ${hours} 小时`;
        } else {
            return `距离现在还有 ${hours} 小时`;
        }
    }
}

// 初始化系统
document.addEventListener('DOMContentLoaded', () => {
    new FansPredictionSystem();
});