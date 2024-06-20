import os
import pandas as pd

def combine_csv_files(input_folder, output_file):
    all_files = []

    # Verificar se o diretório de entrada existe
    if not os.path.isdir(input_folder):
        print(f"Diretório de entrada não encontrado: {input_folder}")
        return

    # Percorrer todas as subpastas e adicionar arquivos CSV à lista
    for root, dirs, files in os.walk(input_folder):
        print(f"Verificando o diretório: {root}")  # Mensagem de depuração
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                all_files.append(file_path)
                print(f"Arquivo encontrado: {file_path}")  # Mensagem de depuração

    # Verificar se algum arquivo CSV foi encontrado
    if not all_files:
        print("Nenhum arquivo CSV encontrado.")
        return

    try:
        # Concatenar todos os arquivos CSV encontrados
        combined_df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
        combined_df.to_csv(output_file, index=False)
        print(f"Dados combinados salvos em {output_file}")
        
        # Verificações adicionais
        print("\nVerificações adicionais:")
        print(f"Número total de linhas: {len(combined_df)}")
        print(f"Número total de colunas: {len(combined_df.columns)}")
        print("Primeiras 5 linhas do DataFrame combinado:")
        print(combined_df.head())

    except Exception as e:
        print(f"Erro ao combinar os arquivos: {e}")

if __name__ == "__main__":
    # Caminho para a pasta que contém as subpastas de cada ano
    input_folder = '../../data/raw/GBPUSD/M1'
    # Caminho para o arquivo de saída combinado
    output_file = '../../data/processed/GBPUSD_M1_combined.csv'
    combine_csv_files(input_folder, output_file)
