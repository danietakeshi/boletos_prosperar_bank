import pandas as pd
import numpy as np

def gerar_tabela_completa(filename: str = 'backup_granatum.csv') -> pd.DataFrame:
    # Lendo CSV de Lançamentos do Granatum
    df = pd.read_csv(f'../update/{filename}', encoding='latin-1', sep=';')

    # Selecionando somente o tipo de pagamento e excluindo o cliente Granatum
    df = df[((df['Forma de pagamento'] == 'Boleto - Granatum Pagamentos') | (df['Forma de pagamento'] == 'Boleto ProsperarBank')) & (df['Cliente/Fornecedor'] != 'GRANATUM LTDA - EPP')]

    # Alterando o valor do boletos para R$ 4,50
    df.loc[df['Categoria'] == '005 - Tx Boleto', 'Valor'] = '4,50'

    # Selecionando as colunas necessárias
    df = df[['Cliente/Fornecedor', 'Data de vencimento', 'Descrição', 'Valor', 'Documento cliente/fornecedor']]

    # Colocando todos os Vencimentos no dia 10
    df['Data de vencimento'] = '10' + df['Data de vencimento'].str[2:]

    # Lendo Lista de Sócios
    df_socios = pd.read_parquet(f'../socios/lista_de_socios.parquet')

    # Unindo as informações das Tabelas de Lançamentos e de Sócios
    df_complete = pd.merge(
        df,
        df_socios,
        how="inner",
        left_on="Cliente/Fornecedor",
        right_on="Nome/Razão Social",
        suffixes=("_x", "_y"),
        copy=True,
        indicator=False,
        validate=None,
    )
    
    return df_complete

def gerar_arquivo_prosperar(df: pd.DataFrame) -> None:
    # Gera Data de Referência
    data_vencimento = df['Data de vencimento'].unique()[0][-4:] + df['Data de vencimento'].unique()[0][3:5] + df['Data de vencimento'].unique()[0][:2]
    
    # Transforma a coluna de Valor em Float
    df['Valor'] = df['Valor'].str.replace(',','.').astype(float)
    
    # Agrupa os Lançamentos por Sócio
    df = df.groupby(['Cliente/Fornecedor', 'Email', 'Documento cliente/fornecedor', 'Endereço', 'Número', 'Bairro', 'Cidade','Estado', 'CEP', 'Data de vencimento'], as_index=False)['Valor'].sum()
    
    # Remove o '.0' dos CEPs
    df['CEP'] = df['CEP'].astype(str).str.replace('.0', '')
    
    # Adiciona coluna de ID Externo
    df['id_aux'] = range(1, 1 + df.shape[0])
    df['id_aux'] = df['id_aux'].map(lambda x: f'{x:0>3}')
    df['ID Externo'] = df['Data de vencimento'].str[-4:] + df['Data de vencimento'].str[3:5] + df['id_aux'].astype(str).str[:]
    df = df.drop(columns=['id_aux'])
    
    # Renomeia colunas existentes
    df = df.rename(columns={
        'ID Externo' : 'ID Externo*',
        'Cliente/Fornecedor' : 'Nome Completo do Pagador (Sacado)*',
        'Email' : 'E-mail*',
        'Documento cliente/fornecedor' : 'CPF/CNPJ*',
        'Endereço' : 'Rua*',
        'Número' : 'Número*',
        'Bairro' : 'Bairro*',
        'Cidade' : 'Cidade*',
        'Estado' : 'Estado*',
        'CEP' : 'Cep*',
        'Data de vencimento' : 'Vencimento*',
        'Valor' : 'Valor (R$)*',
        })
    
    # Adiciona colunas vazias
    for name in [
        'Tipo de Multa',
        'Valor Multa (R$/%)',
        'Tipo Juros Mora',
        'Valor Juros Mora',
        'Tipo de Desconto',
        'Data limite desconto 1',
        'Valor desconto 1 (R$/%)',
        'Data limite desconto 2',
        'Valor desconto 2 (R$/%)',
        'Data limite desconto 3',
        'Valor desconto 3 (R$/%)',
                ]:
        df[name] = np.nan
        
    # Ordena as colunas
    df = df[
        ['ID Externo*',
        'Nome Completo do Pagador (Sacado)*',
        'E-mail*',
        'CPF/CNPJ*',
        'Rua*',
        'Número*',
        'Bairro*',
        'Cidade*',
        'Estado*',
        'Cep*',
        'Vencimento*',
        'Valor (R$)*',
        'Tipo de Multa',
        'Valor Multa (R$/%)',
        'Tipo Juros Mora',
        'Valor Juros Mora',
        'Tipo de Desconto',
        'Data limite desconto 1',
        'Valor desconto 1 (R$/%)',
        'Data limite desconto 2',
        'Valor desconto 2 (R$/%)',
        'Data limite desconto 3',
        'Valor desconto 3 (R$/%)',]
    ]
    
    # Remove o boleto da C. Beatriz
    df = df[df['Nome Completo do Pagador (Sacado)*'] != 'BEATRIZ DA ROSA']
        
    # Exporta no formato Excel
    df.to_excel(f"../boletos/{data_vencimento}_boletos_prosperar.xlsx", sheet_name='boletos', index=False) 
    
if __name__ == '__main__':
    df = gerar_tabela_completa('backup_granatum_20231129.csv')
    gerar_arquivo_prosperar(df)