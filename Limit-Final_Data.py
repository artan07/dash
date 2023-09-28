import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

# Завантажте дані з Excel файлу
df = pd.read_excel('Y:\Reports\CashFlow\Limit-Final_Data.xlsx')

app = dash.Dash(__name__)

# Оформлення додатку
app.layout = html.Div([
    html.H1("Графік сум за категоріями з фільтрами"),

    # Випадаючий список для вибору типу компанії
    dcc.Dropdown(
        id='comp-type-dropdown',
        options=[
            {'label': comp_type, 'value': comp_type}
            for comp_type in df['COMP_TYPE'].unique()
        ],
        multi=True,
        value=df['COMP_TYPE'].unique(),
        placeholder="Виберіть тип компанії"
    ),

    # Випадаючий список для вибору CF_BLOCK
    dcc.Dropdown(
        id='cf-block-dropdown',
        options=[
            {'label': cf_block, 'value': cf_block}
            for cf_block in df['CF_BLOCK'].unique()
        ],
        multi=True,
        placeholder="Виберіть CF_BLOCK"
    ),

    # Вибір періоду
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=df['DATE'].min(),
        end_date=df['DATE'].max(),
        display_format='YYYY-MM-DD',
        clearable=True,
        initial_visible_month=df['DATE'].min(),
    ),

    # Чекбокс для показу за весь рік
    dcc.Checklist(
        id='show-entire-year',
        options=[{'label': 'Показати за весь рік', 'value': 'entire-year'}],
        value=[],
    ),

    # Графік сум за категоріями
    dcc.Graph(id='category-sum-bar-chart'),

    # Кругова діаграма статей витрат
    dcc.Graph(id='expense-category-pie-chart'),

    # Кругова діаграма статей надходжень
    dcc.Graph(id='income-category-pie-chart'),
])

# Функція для оновлення графіків на основі вибору користувача
@app.callback(
    [Output('category-sum-bar-chart', 'figure'),
     Output('expense-category-pie-chart', 'figure'),
     Output('income-category-pie-chart', 'figure')],
    [Input('comp-type-dropdown', 'value'),
     Input('cf-block-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('show-entire-year', 'value')]
)
def update_charts(selected_comp_types, selected_cf_blocks, start_date, end_date, show_entire_year):
    filtered_df = df[(df['COMP_TYPE'].isin(selected_comp_types)) & (df['CF_BLOCK'].isin(selected_cf_blocks))]

    if 'entire-year' in show_entire_year:
        # Вибрана опція показу за весь рік
        filtered_df = filtered_df[(filtered_df['DATE'].dt.year >= df['DATE'].min().year) & (filtered_df['DATE'].dt.year <= df['DATE'].max().year)]
    else:
        # Вибірка за вибраний період
        filtered_df = filtered_df[(filtered_df['DATE'] >= start_date) & (filtered_df['DATE'] <= end_date)]

    filtered_df['Month'] = filtered_df['DATE'].dt.strftime('%Y-%m')
    grouped_df = filtered_df.groupby(['Month', 'STAGE_01'])['HOST_SUMM'].sum().reset_index()

    # Створення графіку сум за категоріями
    fig_bar = go.Figure()

    # Додавання стовбчиків для категорій
    for stage in grouped_df['STAGE_01'].unique():
        stage_data = grouped_df[grouped_df['STAGE_01'] == stage]
        fig_bar.add_trace(
            go.Bar(
                x=stage_data['Month'],
                y=stage_data['HOST_SUMM'],
                name=f'Сума ({stage})'
            )
        )

    # Додавання лінії фінрезультату
    fin_result = filtered_df.groupby(['Month'])['HOST_SUMM'].sum().reset_index()
    fig_bar.add_trace(
        go.Scatter(
            x=fin_result['Month'],
            y=fin_result['HOST_SUMM'],
            mode='lines',
            name='Фінрезультат'
        )
    )

    # Оформлення графіку сум за категоріями
    fig_bar.update_layout(
        title='Графік сум за категоріями (по місяцях) з фільтрами',
        xaxis_title='Місяць',
        yaxis_title='Сума'
    )

    # Створення кругової діаграми статей витрат
    grouped_expense_df = filtered_df[filtered_df['STAGE_01'] == 'Витрати (total)'].groupby(['CF_CATEGORY', 'STAGE_01'])['HOST_SUMM'].sum().reset_index()
    # Змініть знак сум для витрат на додатний
    grouped_expense_df['HOST_SUMM'] = grouped_expense_df['HOST_SUMM'].abs()
    fig_pie_expense = px.pie(
        grouped_expense_df,
        names='CF_CATEGORY',
        values='HOST_SUMM',
        title='Статті витрат',
        hole=0.3,
    )

    # Створення кругової діаграми статей надходжень
    grouped_income_df = filtered_df[filtered_df['STAGE_01'] == 'Надходження (total)'].groupby(['CF_CATEGORY', 'STAGE_01'])['HOST_SUMM'].sum().reset_index()
    fig_pie_income = px.pie(
        grouped_income_df,
        names='CF_CATEGORY',
        values='HOST_SUMM',
        title='Статті надходжень',
        hole=0.3,
    )

    return fig_bar, fig_pie_income, fig_pie_expense

if __name__ == '__main__':
    app.run_server(debug=True)
