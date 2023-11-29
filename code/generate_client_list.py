import pandas as pd

def generate_client_list(filename: str = 'backup_cliente.csv') -> None:
    # Lendo CSV de Sócios do Granatum
    df = pd.read_csv(f'../socios/{filename}', encoding='latin-1', sep=';')

    # Seleciona as colunas necessárias
    df = df[['Nome/Razão Social', 'CPF/CNPJ', 'Email', 'Endereço', 'Número', 'Complemento', 'Bairro', 'Cidade', 'Estado', 'CEP', 'Ativo']]

    # Salva no formato Parquet
    df.to_parquet('lista_de_socios.parquet')

if __name__ == '__main__':
    generate_client_list(filename='backup_cliente_20231129.csv')