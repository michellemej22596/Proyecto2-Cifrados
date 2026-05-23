"use client";

import { useState, useEffect } from "react";
import { api, BlockchainBlock } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Link2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Hash,
  Clock,
  User,
  FileText,
  ArrowRight,
} from "lucide-react";

export function BlockchainExplorer() {
  const [chain, setChain] = useState<BlockchainBlock[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{
    is_valid: boolean;
    total_blocks: number;
    message: string;
  } | null>(null);
  const [expandedBlock, setExpandedBlock] = useState<number | null>(null);
  const [selectedBlock, setSelectedBlock] = useState<BlockchainBlock | null>(null);

  const loadBlockchain = async () => {
    setIsLoading(true);
    try {
      const data = await api.getBlockchain();
      setChain(data.chain);
    } catch (err) {
      console.error("Error loading blockchain:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const verifyChain = async () => {
    setIsVerifying(true);
    try {
      const result = await api.verifyBlockchain();
      setVerificationResult(result);
    } catch (err) {
      console.error("Error verifying blockchain:", err);
    } finally {
      setIsVerifying(false);
    }
  };

  useEffect(() => {
    loadBlockchain();
  }, []);

  const toggleBlock = (index: number) => {
    setExpandedBlock(expandedBlock === index ? null : index);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-xl">
              <Link2 className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Explorador de Blockchain</h2>
              <p className="text-sm text-muted-foreground">
                {chain.length} bloques en la cadena
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadBlockchain} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              Actualizar
            </Button>
            <Button onClick={verifyChain} disabled={isVerifying}>
              {isVerifying ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Verificar
            </Button>
          </div>
        </div>

        {/* Verification Result */}
        {verificationResult && (
          <div
            className={`p-3 rounded-xl flex items-center gap-3 ${
              verificationResult.is_valid
                ? "bg-success/10 border border-success/30"
                : "bg-destructive/10 border border-destructive/30"
            }`}
          >
            {verificationResult.is_valid ? (
              <CheckCircle2 className="h-5 w-5 text-success" />
            ) : (
              <AlertCircle className="h-5 w-5 text-destructive" />
            )}
            <div>
              <p
                className={`font-medium ${
                  verificationResult.is_valid ? "text-success" : "text-destructive"
                }`}
              >
                {verificationResult.is_valid ? "Blockchain Valida" : "Blockchain Invalida"}
              </p>
              <p className="text-sm text-muted-foreground">
                {verificationResult.total_blocks} bloques verificados - {verificationResult.message}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Block List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-pulse text-muted-foreground">Cargando blockchain...</div>
            </div>
          ) : chain.length === 0 ? (
            <div className="text-center py-12">
              <Link2 className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">No hay bloques en la cadena</p>
              <Button variant="outline" onClick={loadBlockchain} className="mt-4">
                Cargar Blockchain
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {chain.map((block, idx) => {
                const isGenesis = block.index === 0;
                const isExpanded = expandedBlock === block.index;
                const isSelected = selectedBlock?.index === block.index;

                return (
                  <div key={block.index}>
                    <div
                      className={`rounded-xl border transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary/10 border-primary/50"
                          : "bg-card border-border hover:border-primary/30"
                      }`}
                      onClick={() => setSelectedBlock(block)}
                    >
                      {/* Block Header */}
                      <div
                        className="p-4 flex items-center justify-between"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleBlock(block.index);
                        }}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-10 h-10 rounded-lg flex items-center justify-center font-mono text-sm ${
                              isGenesis
                                ? "bg-warning/20 text-warning"
                                : "bg-primary/20 text-primary"
                            }`}
                          >
                            #{block.index}
                          </div>
                          <div>
                            <p className="font-medium text-foreground">
                              {isGenesis ? "Bloque Genesis" : `Bloque #${block.index}`}
                            </p>
                            <p className="text-xs text-muted-foreground font-mono">
                              {block.hash.substring(0, 16)}...
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {!isGenesis && block.sender_id && block.sender_id !== "0" && (
                            <span className="text-xs px-2 py-1 bg-secondary rounded-full text-secondary-foreground">
                              {block.sender_id} → {block.recipient_id}
                            </span>
                          )}
                          {isExpanded ? (
                            <ChevronDown className="h-5 w-5 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-5 w-5 text-muted-foreground" />
                          )}
                        </div>
                      </div>

                      {/* Expanded Content */}
                      {isExpanded && (
                        <div className="px-4 pb-4 border-t border-border pt-4 space-y-3">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Hash className="h-3 w-3" /> Indice
                              </p>
                              <p className="font-mono text-sm">{block.index}</p>
                            </div>
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Clock className="h-3 w-3" /> Timestamp
                              </p>
                              <p className="font-mono text-sm">{block.timestamp}</p>
                            </div>
                          </div>

                          {!isGenesis && block.sender_id && block.sender_id !== "0" && (
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-1">
                                <p className="text-xs text-muted-foreground flex items-center gap-1">
                                  <User className="h-3 w-3" /> Remitente ID
                                </p>
                                <p className="font-mono text-sm">{block.sender_id}</p>
                              </div>
                              <div className="space-y-1">
                                <p className="text-xs text-muted-foreground flex items-center gap-1">
                                  <User className="h-3 w-3" /> Destinatario ID
                                </p>
                                <p className="font-mono text-sm">{block.recipient_id}</p>
                              </div>
                            </div>
                          )}

                          {block.message_hash && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <FileText className="h-3 w-3" /> Hash del Mensaje
                              </p>
                              <p className="font-mono text-xs break-all bg-secondary p-2 rounded-lg">
                                {block.message_hash}
                              </p>
                            </div>
                          )}

                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Hash Anterior</p>
                            <p className="font-mono text-xs break-all bg-secondary p-2 rounded-lg">
                              {block.previous_hash}
                            </p>
                          </div>

                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Hash Actual</p>
                            <p className="font-mono text-xs break-all bg-primary/10 p-2 rounded-lg text-primary">
                              {block.hash}
                            </p>
                          </div>

                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Nonce</p>
                            <p className="font-mono text-sm">{block.nonce}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Chain Link Arrow */}
                    {idx < chain.length - 1 && (
                      <div className="flex justify-center py-2">
                        <ArrowRight className="h-4 w-4 text-muted-foreground rotate-90" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Block Detail Panel */}
        {selectedBlock && (
          <div className="w-80 border-l border-border bg-card p-4 overflow-y-auto hidden lg:block">
            <h3 className="font-semibold text-foreground mb-4">Detalles del Bloque</h3>
            
            <div className="space-y-4">
              <div
                className={`p-4 rounded-xl ${
                  selectedBlock.index === 0
                    ? "bg-warning/10 border border-warning/30"
                    : "bg-primary/10 border border-primary/30"
                }`}
              >
                <p className="text-2xl font-bold text-center">
                  #{selectedBlock.index}
                </p>
                <p className="text-center text-sm text-muted-foreground">
                  {selectedBlock.index === 0 ? "Genesis Block" : "Transaction Block"}
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Timestamp</p>
                  <p className="text-sm font-mono">{selectedBlock.timestamp}</p>
                </div>

                {selectedBlock.sender_id && selectedBlock.sender_id !== "0" && (
                  <>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Transaccion</p>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="px-2 py-1 bg-secondary rounded">
                          User {selectedBlock.sender_id}
                        </span>
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                        <span className="px-2 py-1 bg-secondary rounded">
                          User {selectedBlock.recipient_id}
                        </span>
                      </div>
                    </div>

                    {selectedBlock.message_hash && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Message Hash</p>
                        <p className="text-xs font-mono break-all p-2 bg-secondary rounded-lg">
                          {selectedBlock.message_hash}
                        </p>
                      </div>
                    )}
                  </>
                )}

                <div>
                  <p className="text-xs text-muted-foreground mb-1">Previous Hash</p>
                  <p className="text-xs font-mono break-all p-2 bg-secondary rounded-lg">
                    {selectedBlock.previous_hash}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-muted-foreground mb-1">Block Hash</p>
                  <p className="text-xs font-mono break-all p-2 bg-primary/10 rounded-lg text-primary">
                    {selectedBlock.hash}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-muted-foreground mb-1">Nonce</p>
                  <p className="text-sm font-mono">{selectedBlock.nonce}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
