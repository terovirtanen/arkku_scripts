document.addEventListener('DOMContentLoaded', () => {
    const energyFileInput = document.getElementById('energyFile');
    const priceMarginInput = document.getElementById('priceMargin');
    const priceFixedInput = document.getElementById('priceFixed');
    const generateButton = document.getElementById('generateButton');
    const ctxMonthly = document.getElementById('monthlyChart').getContext('2d');
    const ctxYearly = document.getElementById('yearlyChart').getContext('2d');
    let monthlyChart;
    let yearlyChart;

    generateButton.addEventListener('click', async () => {
        // Clear existing table and chart data
        document.getElementById('monthlyTable').innerHTML = '';
        document.getElementById('yearlyTable').innerHTML = '';
        if (monthlyChart) {
            monthlyChart.destroy();
        }
        if (yearlyChart) {
            yearlyChart.destroy();
        }

        const energyFile = energyFileInput.files[0];
        const priceFile = priceFileContent;
        const priceMargin = parseFloat(priceMarginInput.value);
        const priceFixed = parseFloat(priceFixedInput.value);

        const energyData = await fetchEnergyData(energyFile);
        const priceData = await readPriceCSV(priceFile);

        // Combine energyData and priceData based on date
        const combinedData = combineData(energyData, priceData);
        const dataOptimized = optimizedData(combinedData);

        generateMonthlyTable(combinedData, dataOptimized, priceMargin, priceFixed);
        generateYearlyTable(combinedData, dataOptimized, priceMargin, priceFixed);
        monthlyChart = generateAveragePriceChart(combinedData, ctxMonthly, priceMargin, priceFixed);
        yearlyChart = generateAverageYearlyPriceChart(combinedData, ctxYearly, priceMargin, priceFixed);

    });

    async function fetchEnergyData(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (event) => {
                const fileType = file.name.split('.').pop().toLowerCase();
                if (fileType === 'csv') {
                    const text = event.target.result;
                    const data = parseEnergyCSV(text);
                    resolve(data);
                } else if (fileType === 'xlsx') {
                    const dataIn = new Uint8Array(event.target.result);
                    const workbook = XLSX.read(dataIn, { type: 'array' });
                    const sheetName = workbook.SheetNames[0];
                    const worksheet = workbook.Sheets[sheetName];
                    const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
                    const data = parseEnergyXLSX(jsonData);
                    resolve(data);
                } else {
                    reject(new Error('Tuntematon tiedostotyyppi'));
                }
            };
            reader.onerror = (error) => reject(error);
            if (file.name.split('.').pop().toLowerCase() === 'csv') {
                reader.readAsText(file);
            } else {
                reader.readAsArrayBuffer(file);
            }
        });
    }

    function parseEnergyXLSX(data) {
        const headers = data[0];
        const dateIndex = headers.indexOf("Ajankohta");
        const energyIndex = headers.indexOf("Laskutettava kulutus (kWh)");

        return data.slice(1).map(row => { // Skip the header line
            const date = row[dateIndex];
            const energy = row[energyIndex];
            const formattedDate = parseEnergyDate(date);
            return {
                date: formattedDate,
                energy: energy ? parseFloat(String(energy).replace(',', '.')) : undefined
            };
        });
    }

    async function readPriceCSV(file) {
        if (typeof file === 'string') {
            return parsePriceCSV(file);
        } else {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const text = event.target.result;
                    const data = parsePriceCSV(text);
                    resolve(data);
                };
                reader.onerror = (error) => reject(error);
                reader.readAsText(file);
            });
        }
    }

    function parseEnergyCSV(text) {
        // FinGrid CSV format:
        // Mittauspisteen tunnus;Tuotteen tyyppi;Resoluutio;Yksikkötyyppi;Lukeman tyyppi;Alkuaika;Määrä;Laatu
        // 643003825107340356;8716867000030;PT15M;kWh;BN01;2024-12-31T22:00:00Z;0,150000;OK

        const lines = text.split('\n').filter(line => line.trim() !== '');
        if (lines.length === 0) return [];
        
        // Parse header row
        const headers = lines[0].split(';');
        const dateIndex = headers.indexOf('Alkuaika');
        const energyIndex = headers.indexOf('Määrä');
        
        // Parse data rows (skip header)
        const data = lines.slice(1).map(line => {
            const columns = line.split(';');
            const dateString = columns[dateIndex];
            const energyString = columns[energyIndex];
            
            return {
                date: new Date(dateString),
                energy: energyString ? parseFloat(energyString.replace(',', '.')) : undefined
            };
        });
        
        return data;
    }
    //parseEnergyDate('31.01.2021 00:00');
    function parseEnergyDate(dateString) {
        const [day, month, yearAndTime] = dateString.split('.');
        const [year, hourAndMinute] = yearAndTime.split(' ');
        const [hour, minute] = hourAndMinute.split(':');
        return new Date(year, month-1, day, hour, minute);
    }

    function parsePriceCSV(text) {
        const lines = text.split('\n');
        const data = lines.map(line => {
            const [date, price] = line.split(';');
            const formattedDate = parsePriceDate(date);
            const formattedPrice = price ? parseFloat(price.replace(',', '.').replace('−', '-')) : undefined; // Replace non-standard minus sign
            return {
                date: formattedDate,
                price: formattedPrice
            };
        });
        return data;
    }
    //parseEnergyDate('30/12/2024 03:59:11');
    function parsePriceDate(dateString) {
        const [day, month, yearAndTime] = dateString.split('/');
        const [year, hourAndMinute] = yearAndTime.split(' ');
        const [hour, minute] = hourAndMinute.split(':');
        return new Date(year, month-1, day, hour, minute);
    }


    function combineData(energyData, priceData) {
        const combinedData = energyData.map(energyEntry => {
            const priceEntry = priceData.find(priceEntry => priceEntry.date.getTime() === energyEntry.date.getTime());
            return {
                ...energyEntry,
                price: priceEntry ? priceEntry.price : undefined
            };
        });
        return combinedData;
    }

    function generateMonthlyTable(data, dataOptimized, priceMargin, priceFixed) {
        const monthlyTable = document.getElementById('monthlyTable');
        monthlyTable.innerHTML = '';

        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>Kuukausi</th><th>Kulutettu energia (kWh)</th><th>Keskihinta pörssisähköllä (c/kWh)</th><th>Hinta pörssisähköllä (€)</th><th>Hinta optimoituna (€)</th><th>Kiinteähinta (€)</th>';
        monthlyTable.appendChild(headerRow);

        const monthlyData = data.reduce((acc, entry) => {
            const month = entry.date.getMonth();
            const year = entry.date.getFullYear();
            const key = `${year}-${month}`;
            if (!acc[key]) {
                acc[key] = { date: new Date(year, month), energy: 0, totalCost: 0, totalCostOpt: 0, totalCostFixed: 0 };
            }
            acc[key].energy += entry.energy || 0;
            acc[key].totalCost += ((entry.price || 0) + priceMargin) * (entry.energy || 0);
            entryOpt = dataOptimized.find(optEntry => optEntry.date.getTime() === entry.date.getTime());
            acc[key].totalCostOpt += ((entryOpt.price || 0) + priceMargin) * (entryOpt.energy || 0);
            acc[key].totalCostFixed += priceFixed * (entry.energy || 0);
            return acc;
        }, {});

        Object.values(monthlyData).forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `<td>${entry.date.toLocaleDateString('fi-FI', { year: 'numeric', month: 'long' })}</td>
                             <td>${entry.energy.toFixed(2)}</td>
                             <td>${(entry.totalCost / entry.energy ).toFixed(2)}</td>
                             <td>${(entry.totalCost / 100).toFixed(2)}</td>
                             <td>${(entry.totalCostOpt / 100).toFixed(2)}</td>
                             <td>${(entry.totalCostFixed / 100).toFixed(2)}</td>`;
            monthlyTable.appendChild(row);
        });
    }

    function generateYearlyTable(data, dataOptimized, priceMargin, priceFixed) {
        const yearlyTable = document.getElementById('yearlyTable');
        yearlyTable.innerHTML = '';

        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>Vuosi</th><th>Kulutettu energia (kWh)</th><th>Keskihinta pörssisähköllä (c/kWh)</th><th>Hinta pörssisähköllä (€)</th><th>Hinta optimoituna (€)</th><th>Kiinteähinta (€)</th>';
        yearlyTable.appendChild(headerRow);

        const yearlyData = data.reduce((acc, entry) => {
            const year = entry.date.getFullYear();
            if (!acc[year]) {
                acc[year] = { date: new Date(year, 0), energy: 0, totalCost: 0, totalCostOpt: 0, totalCostFixed: 0 };
            }
            acc[year].energy += entry.energy || 0;
            acc[year].totalCost += ((entry.price || 0) + priceMargin) * (entry.energy || 0);
            entryOpt = dataOptimized.find(optEntry => optEntry.date.getTime() === entry.date.getTime());
            acc[year].totalCostOpt += ((entryOpt.price || 0) + priceMargin) * (entryOpt.energy || 0);
            acc[year].totalCostFixed += priceFixed * (entry.energy || 0);
            return acc;
        }, {});

        Object.values(yearlyData).forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `<td>${entry.date.getFullYear()}</td>
                             <td>${entry.energy.toFixed(2)}</td>
                             <td>${(entry.totalCost / entry.energy ).toFixed(2)}</td>
                             <td>${(entry.totalCost / 100).toFixed(2)}</td>
                             <td>${(entry.totalCostOpt / 100).toFixed(2)}</td>
                             <td>${(entry.totalCostFixed / 100).toFixed(2)}</td>`;
            yearlyTable.appendChild(row);
        });
    }

    function optimizedData(data) {
        let optimizedData = [];
    
        // Group data by day
        const groupedData = data.reduce((acc, entry) => {
            const dateKey = new Date(entry.date.getTime() - entry.date.getTimezoneOffset() * 60000).toISOString().split('T')[0]; // Get date part only in Finnish time
            if (!acc[dateKey]) {
                acc[dateKey] = [];
            }
            acc[dateKey].push(entry);
            return acc;
        }, {});
        // Process each day's data
        Object.values(groupedData).forEach(dayData => {
            // Sort by price ascending
            const sortedByPrice = [...dayData].sort((a, b) => a.price - b.price);
            // Sort by energy descending
            const sortedByEnergy = [...dayData].sort((a, b) => b.energy - a.energy);
            // Swap prices and energies
            const optimizedDayData = sortedByPrice.map((entry, index) => ({
                ...entry,
                energy: sortedByEnergy[index].energy
            }));
    
            optimizedData = optimizedData.concat(optimizedDayData);
        });
        return optimizedData;
    }

    function generateAverageYearlyPriceChart(data, ctx, priceMargin, priceFixed) {
        const yearlyData = data.reduce((acc, entry) => {
            const year = entry.date.getFullYear();
            if (!acc[year]) {
                acc[year] = { date: new Date(year, 0), energy: 0, totalCost: 0 };
            }
            acc[year].energy += entry.energy || 0;
            acc[year].totalCost += ((entry.price || 0) + priceMargin) * (entry.energy || 0);

            return acc;
        }, {});

        const labels = Object.values(yearlyData).map(entry => entry.date.getFullYear());
        const averagePrices = Object.values(yearlyData).map(entry => (entry.totalCost / entry.energy).toFixed(2));

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Keskihinta (c/kWh)',
                        data: averagePrices,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'Kiinteä hinta (c/kWh)',
                        data: new Array(labels.length).fill(priceFixed),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1,
                        type: 'line',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Vuosi'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Keskihinta (c/kWh)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'black'
                        }
                    }
                },
                layout: {
                    backgroundColor: 'white'
                },
                elements: {
                    line: {
                        borderWidth: 3,
                        tension: 0.4
                    },
                    point: {
                        radius: 0
                    }
                }
            }
        });
    }

    function generateAveragePriceChart(data, ctx, priceMargin, priceFixed) {
        const monthlyData = data.reduce((acc, entry) => {
            const month = entry.date.getMonth();
            const year = entry.date.getFullYear();
            const key = `${year}-${month}`;
            if (!acc[key]) {
                acc[key] = { date: new Date(year, month), energy: 0, totalCost: 0  };
            }
            acc[key].energy += entry.energy || 0;
            acc[key].totalCost += ((entry.price || 0) + priceMargin) * (entry.energy || 0);

            return acc;
        }, {});

        const labels = Object.values(monthlyData).map(entry => entry.date.toLocaleDateString('fi-FI', { year: 'numeric', month: 'long' }));
        const averagePrices = Object.values(monthlyData).map(entry => (entry.totalCost / entry.energy).toFixed(2));

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Keskihinta (c/kWh)',
                        data: averagePrices,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'Kiinteähinta (c/kWh)',
                        data: new Array(labels.length).fill(priceFixed),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1,
                        type: 'line',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Kuukausi'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Keskihinta (c/kWh)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'black'
                        }
                    }
                },
                layout: {
                    backgroundColor: 'white'
                },
                elements: {
                    line: {
                        borderWidth: 3,
                        tension: 0.4
                    },
                    point: {
                        radius: 0
                    }
                }
            }
        });
    }

});