
const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

// Load env from project root
dotenv.config({ path: path.resolve(__dirname, '../.env') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error("Missing Supabase credentials in .env");
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function runDebug() {
    console.log("--- DEBUGGING PAGE QUERY ---");
    
    // 1. Replicate qNew Count
    console.log("\n[1] Testing COUNT query...");
    const selectCount = 'count, unidade:nexus_unidades!inner(id)';
    const { count, error: countError } = await supabase
        .from('nexus_modelos')
        .select(selectCount, { count: 'exact', head: true })
        .eq('status', 'Ativo');
        
    if (countError) console.error("Count Error:", countError);
    console.log("Count Result:", count);

    // 2. Replicate qNew Data
    console.log("\n[2] Testing DATA query...");
    // Emulating page.tsx logic
    const selectData = '*, unidade:nexus_unidades!inner(*), consultor:nexus_participantes(*)';
    
    const { data, error, count: dataCount } = await supabase
        .from('nexus_modelos')
        .select(selectData)
        .eq('status', 'Ativo')
        .range(0, 11) // First page
        .order('data', { ascending: false });

    if (error) {
        console.error("❌ Data Query FAILED:", error);
    } else {
        console.log(`✅ Data Query Success. Returned ${data.length} rows.`);
        if (data.length > 0) {
            console.log("Sample Row 0:", JSON.stringify(data[0], null, 2));
        } else {
            console.warn("⚠ Returned 0 rows despite Count being", count);
        }
    }
    
    // 3. Test simpler query if DATA failed/empty
    if (!data || data.length === 0) {
        console.log("\n[3] Testing Simplified Data query (No joins)...");
        const { data: dSimple } = await supabase
             .from('nexus_modelos')
             .select('*')
             .eq('status', 'Ativo')
             .limit(5);
        console.log(`Simple Check: ${dSimple ? dSimple.length : 0} rows found without joins.`);
        if (dSimple && dSimple.length > 0) {
             const sample = dSimple[0];
             console.log("Sample Simple:", sample);
             // Check FKs
             console.log(`Check FKs -> Unidade: ${sample.unidade}, Consultor: ${sample.consultor_venda}`);
        }
    }
}

runDebug();
