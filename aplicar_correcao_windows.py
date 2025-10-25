#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script auxiliar para aplicar correção no Windows.
Garante encoding correto UTF-8.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def main():
    print("\n" + "="*70)
    print("🔧 APLICANDO CORREÇÃO - PROCESSAMENTO PARALELO")
    print("="*70)
    
    # Caminhos
    source_file = Path("backend_agents_guias_graph_FIXED.py")
    target_file = Path("backend/agents/guias/graph.py")
    
    # Validações
    print("\n🔍 Validando arquivos...")
    
    if not source_file.exists():
        print(f"❌ Arquivo fonte não encontrado: {source_file}")
        print("\n📥 Certifique-se de que o arquivo backend_agents_guias_graph_FIXED.py")
        print("   está no diretório raiz do projeto.")
        return False
    
    if not target_file.exists():
        print(f"❌ Arquivo alvo não encontrado: {target_file}")
        print("\n📁 Verifique se está executando no diretório raiz do projeto.")
        return False
    
    print(f"✅ Arquivo fonte: {source_file}")
    print(f"✅ Arquivo alvo: {target_file}")
    
    # Backup
    print("\n💾 Criando backup...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = target_file.with_suffix(f'.py.backup_{timestamp}')
    
    try:
        shutil.copy2(target_file, backup_file)
        print(f"✅ Backup criado: {backup_file}")
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False
    
    # Copiar arquivo corrigido
    print("\n📝 Aplicando correção...")
    
    try:
        # Lê arquivo fonte em UTF-8
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Escreve arquivo alvo em UTF-8
        with open(target_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        
        print(f"✅ Correção aplicada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao copiar arquivo: {e}")
        print(f"\n🔄 Restaurando backup...")
        
        try:
            shutil.copy2(backup_file, target_file)
            print("✅ Backup restaurado")
        except Exception as e2:
            print(f"❌ ERRO CRÍTICO: Não foi possível restaurar backup: {e2}")
            print(f"   Restaure manualmente: {backup_file} -> {target_file}")
        
        return False
    
    # Validação
    print("\n🔍 Validando correção...")
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            new_content = f.read()
        
        # Verifica marcadores da correção
        checks = {
            "processar_topicos_paralelo": "processar_topicos_paralelo" in new_content,
            "asyncio.gather": "asyncio.gather" in new_content,
            "Semaphore": "Semaphore" in new_content,
            "modo paralelo": 'modo.lower() == "paralelo"' in new_content,
        }
        
        print("\n✅ Marcadores encontrados:")
        all_ok = True
        
        for check_name, check_result in checks.items():
            emoji = "✅" if check_result else "❌"
            print(f"   {emoji} {check_name}")
            if not check_result:
                all_ok = False
        
        if not all_ok:
            print("\n⚠️ AVISO: Alguns marcadores não encontrados!")
            print("   A correção pode não ter sido aplicada corretamente.")
            return False
        
        print(f"\n✅ Arquivo validado: {len(new_content)} caracteres")
        
    except Exception as e:
        print(f"❌ Erro ao validar: {e}")
        return False
    
    # Limpeza de cache
    print("\n🧹 Limpando cache Python...")
    
    try:
        import subprocess
        
        # Remove __pycache__
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                cache_dir = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(cache_dir)
                    print(f"   🗑️ Removido: {cache_dir}")
                except:
                    pass
        
        # Remove .pyc
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass
        
        print("✅ Cache limpo")
        
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível limpar todo o cache: {e}")
        print("   Execute manualmente se necessário:")
        print("   - PowerShell: Get-ChildItem -Recurse __pycache__ | Remove-Item -Recurse -Force")
    
    # Conclusão
    print("\n" + "="*70)
    print("🎉 CORREÇÃO APLICADA COM SUCESSO!")
    print("="*70)
    
    print(f"\n📝 Resumo:")
    print(f"   ✅ Backup: {backup_file}")
    print(f"   ✅ Arquivo corrigido: {target_file}")
    print(f"   ✅ Encoding: UTF-8")
    
    print(f"\n🚀 Próximos passos:")
    print(f"   1. Reinicie o servidor: python run.py")
    print(f"   2. Execute os testes: python test_parallel_fix.py")
    print(f"   3. Teste com seu YAML via interface web")
    
    print("\n💡 Para reverter:")
    print(f"   copy \"{backup_file}\" \"{target_file}\"")
    
    print("\n" + "="*70 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print("✅ Script concluído com sucesso!\n")
            exit(0)
        else:
            print("❌ Script falhou. Revise os erros acima.\n")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário\n")
        exit(1)
        
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)